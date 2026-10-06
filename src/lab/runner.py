"""GUIDE Phần 1 - Chạy một tác vụ (task) và ghi kết quả.   >>> SINH VIÊN CÀI ĐẶT run_task <<<

Pseudo-code: guides/pseudocode/03_runner.md
Kiểm tra:    pytest tests/test_03_runner.py
Chạy thật:   python -m lab.runner --condition baseline --tasks learn
"""
import argparse
import json
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import AIMessage, ToolMessage

from .agent import build_agent
from .grading import grade                                                      # có sẵn
from .tasks import ROOT, get_task, hash_dir, list_tasks, prepare_sandbox         # có sẵn

# Ba điều kiện thí nghiệm (condition). `skills_dir` là thư mục skill nguồn (tính từ thư mục gốc của lab).
CONDITIONS = {
    "baseline": {"mode": "single", "skills_dir": None},
    "subagents": {"mode": "subagents", "skills_dir": None},
    "skills-auto": {"mode": "single", "skills_dir": "skills/auto"},
}

# Common execution guidance: no task answers or hidden reporting conventions.
# Apply equally to all conditions so baseline also gets reliable execution.
EXECUTION_NOTE = (
    "\n\nExecution requirements: Read the workspace README, task specifications, "
    "and relevant source/docstrings before implementation. Use the documented "
    "formats and semantics rather than guessing. For data transformations, "
    "write a Python script using write_file and execute it with python. Read "
    "the complete input programmatically; do not transcribe preview rows or "
    "estimate results mentally. Prefer standard-library modules and Decimal "
    "for monetary arithmetic, preserving the required output units. "
    "Keep imports at module scope. After a failed command, read the traceback "
    "and the current affected function before editing. If a patch fails or "
    "the same error recurs, replace the complete affected function from its "
    "current contents instead of repeating an ineffective edit. "
    "Before finishing, execute validation: reopen each required output file, "
    "check schema, types and counts against the available instructions, and "
    "run the relevant tests for code changes. Fix concrete validation failures. "
    "Only claim outputs that exist and checks that actually ran."
)


def render_trace(messages) -> str:
    """CÓ SẴN, KHÔNG SỬA. Chuyển danh sách message của luồng chính thành Markdown (vết - trace).

    Lưu ý: chỉ gồm luồng chính. Việc subagent làm bên trong KHÔNG hiện trong vết;
    chỉ thấy lệnh gọi `task` và báo cáo cuối của subagent.
    """
    home = str(Path.home())

    def clean(text) -> str:
        return str(text).replace(home, "~")[:1500]

    parts = []
    for m in messages:
        if isinstance(m, AIMessage):
            if m.content:
                parts.append(f"### Assistant\n{clean(m.content)}")
            for tc in m.tool_calls:
                parts.append(f"### Tool call: {tc['name']}\n{clean(json.dumps(tc['args'], ensure_ascii=False))}")
        elif isinstance(m, ToolMessage):
            parts.append(f"### Tool result\n{clean(m.content)}")
        else:
            parts.append(f"### {m.type.capitalize()}\n{clean(m.content)}")
    return "\n\n".join(parts)


def run_task(task_id: str, condition: str, results_dir="results", model=None, recursion_limit: int = 60) -> dict:
    """Chạy MỘT tác vụ dưới MỘT điều kiện, chấm điểm, ghi kết quả, và trả về bản ghi (record).

    Ghi vào: <results_dir>/<condition>/<task_id>/run.json và trace.md  (trace.md = render_trace(messages)).
    Bản ghi `run.json` phải có các khóa:
      task, condition, role, score, passed, total, checks,
      tokens {input, output, total}       - cộng dồn mọi lần gọi LLM, kể cả subagent (dùng UsageMetadataCallbackHandler)
      tool_calls                          - số tool call trong các AIMessage của luồng chính (không gồm việc bên trong subagent)
      subagent_calls                      - số tool call có tên "task" (giao việc cho subagent)
      skills_read                         - số skill KHÁC NHAU đã được đọc: với mỗi tool call "read_file" có file_path chứa
                                            "skills/", lấy tên thư mục ngay sau "skills/" rồi đếm các tên khác nhau
                                            (đọc lại cùng một skill chỉ tính một lần)
      skills_modified (bool)              - thư mục skills trong sandbox bị đổi trong lúc chạy (so hash_dir trước/sau)
      skills_sha256                       - hash_dir(sandbox/"skills") TRƯỚC khi chạy (để đối chiếu với skill đã đóng băng)
      timestamp                           - thời điểm bắt đầu, UTC, dạng ISO-8601
      seconds, final_message, error (None nếu không lỗi)
    Lỗi khi chạy tác tử KHÔNG được làm chương trình dừng: ghi vào `error` và vẫn chấm điểm.
    Sandbox là thư mục tạm NGOÀI kho mã nguồn và phải được xóa sau khi chạy.
    """
    cfg = CONDITIONS[condition]
    task = get_task(task_id)
    skills_dir = ROOT / cfg["skills_dir"] if cfg["skills_dir"] else None
    out = Path(results_dir) / condition / task_id
    out.mkdir(parents=True, exist_ok=True)
    # Windows' default TEMP is on C:, which can be full even when the
    # project drive has space. Keep disposable sandboxes outside the repo.
    sandbox_root = os.environ.get("LAB_SANDBOX_ROOT")
    if sandbox_root is None and os.name == "nt":
        sandbox_root = str(ROOT.parent / ".agent-lab-tmp")
    if sandbox_root:
        Path(sandbox_root).mkdir(parents=True, exist_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix="agent-lab-", dir=sandbox_root))
    record = {
        "task": task.id,
        "condition": condition,
        "role": task.role,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    messages = []
    try:
        prepare_sandbox(task, sandbox, skills_dir)
        before_hash = hash_dir(sandbox / "skills")
        record["skills_sha256"] = before_hash
        usage = UsageMetadataCallbackHandler()
        started = time.monotonic()
        try:
            agent = build_agent(
                sandbox,
                mode=cfg["mode"],
                use_skills=skills_dir is not None,
                model=model,
            )
            instruction = task.instruction + EXECUTION_NOTE
            if skills_dir is not None:
                paths = sorted((sandbox / "skills").glob("*/SKILL.md"))
                if paths:
                    instruction += (
                        "\n\nBefore doing this task, read the applicable SKILL.md using read_file. "
                        "It contains the Acme reporting conventions required above. Available files:\n"
                        + "\n".join(path.relative_to(sandbox).as_posix() for path in paths)
                        + "\nApply the skill's output schema and validate every required artifact before finishing."
                    )
            for state in agent.stream(
                {"messages": [{"role": "user", "content": instruction}]},
                config={"callbacks": [usage], "recursion_limit": recursion_limit},
                stream_mode="values",
            ):
                messages = list(state.get("messages", messages))
                # Persist the last completed graph step, including before an
                # API error or recursion-limit exception interrupts the run.
                (out / "trace.md").write_text(render_trace(messages), encoding="utf-8")
            final = str(messages[-1].content) if messages else ""
            last = messages[-1] if messages else None
            record["finish_reason"] = (
                last.response_metadata.get("finish_reason") if isinstance(last, AIMessage) else None
            )
            if isinstance(last, AIMessage) and last.invalid_tool_calls:
                raise RuntimeError("Model returned invalid tool calls; inspect trace and model output limits")
            if record["finish_reason"] in {"length", "max_tokens", "content_filter"}:
                raise RuntimeError(f"Model response stopped early: {record['finish_reason']}")
            if not isinstance(last, AIMessage) or not final.strip() or last.tool_calls:
                raise RuntimeError("Agent ended without a non-empty final answer")
        except Exception as exc:  # noqa: BLE001
            record["error"] = f"{type(exc).__name__}: {exc}"
            final = ""

        record["seconds"] = round(time.monotonic() - started, 1)
        totals = {"input": 0, "output": 0, "total": 0}
        for item in usage.usage_metadata.values():
            totals["input"] += item.get("input_tokens", 0)
            totals["output"] += item.get("output_tokens", 0)
            totals["total"] += item.get("total_tokens", 0)
        record["tokens"] = totals

        calls = [tc for message in messages if isinstance(message, AIMessage) for tc in message.tool_calls]
        skills_read = set()
        for call in calls:
            if call.get("name") != "read_file":
                continue
            path = str(call.get("args", {}).get("file_path", "")).replace("\\", "/").lstrip("/")
            parts = path.split("/")
            if "skills" in parts:
                index = parts.index("skills")
                if index + 1 < len(parts):
                    skills_read.add(parts[index + 1])
        record.update({
            "tool_calls": len(calls),
            "subagent_calls": sum(call.get("name") == "task" for call in calls),
            "skills_read": len(skills_read),
            "skills_modified": hash_dir(sandbox / "skills") != before_hash,
            "final_message": final,
        })
        grading = grade(task, sandbox / "workspace")
        grading_error = grading.pop("error", None)
        if grading_error:
            record["grading_error"] = grading_error
            record["error"] = record["error"] or grading_error
        record.update(grading)
        # Retain generated artifacts for diagnosing failed checks after the
        # temporary sandbox is removed. Never copy the sandbox environment.
        shutil.copytree(sandbox / "workspace", out / "workspace", dirs_exist_ok=True)
        (out / "trace.md").write_text(render_trace(messages), encoding="utf-8")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)

    (out / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def main(argv=None):
    """CÓ SẴN, KHÔNG SỬA. Giao diện dòng lệnh (CLI): --condition, --tasks (id... | all | learn | eval), --results, --recursion-limit.

    In mỗi lần chạy một dòng: điều kiện, id, passed/total, token, số tool call, số giây, lỗi (nếu có).
    """
    ap = argparse.ArgumentParser(description="Run tasks under one condition.")
    ap.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    ap.add_argument("--tasks", nargs="+", default=["all"], help="task ids, or 'all', 'learn', 'eval'")
    ap.add_argument("--results", default="results")
    ap.add_argument("--recursion-limit", type=int, default=60)
    args = ap.parse_args(argv)
    if args.tasks == ["all"]:
        ids = [t.id for t in list_tasks()]
    elif args.tasks in (["learn"], ["eval"]):
        ids = [t.id for t in list_tasks(args.tasks[0])]
    else:
        ids = args.tasks
    for tid in ids:
        try:
            r = run_task(tid, args.condition, args.results, recursion_limit=args.recursion_limit)
        except Exception as exc:  # noqa: BLE001
            print(f"{args.condition:13s} {tid:11s} CRASH {type(exc).__name__}: {exc}", flush=True)
            continue
        print(f"{args.condition:13s} {tid:11s} score={r['passed']}/{r['total']} tokens={r['tokens']['total']} "
              f"calls={r['tool_calls']} {r['seconds']}s" + (f" ERROR={r['error']}" if r["error"] else ""), flush=True)


if __name__ == "__main__":
    main()
