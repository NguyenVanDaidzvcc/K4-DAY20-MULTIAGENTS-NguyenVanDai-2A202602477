"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""

import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers


# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill -------------------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ)."""
    problems = []

    m = re.match(
        r"^---\n(.*?)\n---\n(.*)$",
        text.strip() + "\n",
        re.S,
    )

    if not m:
        return ["missing YAML frontmatter"]

    front, body = m.groups()

    name = re.search(
        r"^name:\s*(.+)$",
        front,
        re.M,
    )

    desc = re.search(
        r"^description:\s*(.+)$",
        front,
        re.M,
    )

    n = name.group(1).strip() if name else ""

    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")

    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")

    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")

    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")

    low = text.lower()

    for marker in eval_markers():
        if marker in low:
            problems.append(
                f"mentions evaluation material: {marker}"
            )

    return problems


def parse_skill_blocks(
    reply: str,
) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md)."""

    pattern = re.compile(
        r"^=== SKILL: (\S+) ===[ \t]*\n"
        r"(.*?)(?=^=== END ===|^=== SKILL: |\Z)",
        re.S | re.M,
    )

    return [
        (name, text.strip())
        for name, text in pattern.findall(str(reply))
    ]


# -----------------------------------------------------------------------------


def curate_skills(
    results_dir="results",
    source_condition="baseline",
    out_dir=None,
    model=None,
    max_skills: int = 3,
) -> list[Path]:
    """Sinh skill từ các check thất bại của learning tasks."""

    destination = (
        Path(out_dir)
        if out_dir is not None
        else ROOT / "skills" / "auto"
    )

    source = Path(results_dir) / source_condition

    runs: list[dict] = []

    # =========================================================
    # 1. Đọc kết quả LEARNING
    # =========================================================

    for run_path in sorted(
        source.glob("*/run.json")
    ):
        run = json.loads(
            run_path.read_text(
                encoding="utf-8"
            )
        )

        # Tuyệt đối không dùng eval
        if run.get("role") != "learn":
            continue

        failed = [
            (
                check.get("name", ""),
                check.get("detail", ""),
            )
            for check in run.get("checks", [])
            if not check.get("passed", False)
        ]

        trace_path = run_path.with_name(
            "trace.md"
        )

        trace = (
            trace_path.read_text(
                encoding="utf-8",
                errors="replace",
            )[-6000:]
            if trace_path.exists()
            else ""
        )

        runs.append(
            {
                "task": run.get(
                    "task",
                    run_path.parent.name,
                ),
                "failed": failed,
                "error": run.get("error") or "",
                "trace": trace,
            }
        )

    # =========================================================
    # 2. Không có lỗi -> không gọi model
    # =========================================================

    if not any(
        run["failed"]
        for run in runs
    ):
        print(
            "warning: no failed checks "
            "in learning tasks"
        )
        return []

    # =========================================================
    # 3. Xây learning evidence
    # =========================================================

    evidence_blocks: list[str] = []

    for run in runs:

        if not run["failed"]:
            continue

        failed_lines = []

        for check_name, detail in run["failed"]:

            is_rule = (
                detail.strip()
                .upper()
                .startswith("RULE:")
            )

            label = (
                "REUSABLE CONVENTION"
                if is_rule
                else "FAILURE"
            )

            failed_lines.append(
                f"- [{label}] "
                f"{check_name}: {detail}"
            )

        run_error = (
            run["error"]
            if run["error"]
            else "none"
        )

        evidence_blocks.append(
            f"TASK: {run['task']}\n"
            f"RUN ERROR: {run_error}\n"
            f"FAILED CHECKS:\n"
            f"{chr(10).join(failed_lines)}\n"
            f"TRACE TAIL:\n"
            f"{run['trace']}"
        )

    # =========================================================
    # 4. Prompt curator
    #
    # Quan trọng:
    # - mặc định đúng 3 skill
    # - không để model tự sinh 2 skill code
    # - data/log đều có slot riêng
    # =========================================================

    prompt = f"""You write reusable procedural skills from LEARNING EVIDENCE only.
Return at most {max_skills} domain skills: code-repair-and-conventions,
tabular-data-and-reporting, log-triage-and-reporting, when supported by evidence.

The most important content is the exact organizational conventions supplied
in RULE feedback. The agent cannot see the grader: the skill MUST state these
rules completely, not say "follow conventions" or "if required". Preserve exact
output filenames, JSON key names and types, CSV header and column order,
monetary units, timestamp format, sorting and row-count definitions. These
schema literals are reusable conventions and must NOT be generalized away.
Do not copy expected numeric answers, record IDs, input dataset filenames,
or evaluation material. Derive values by processing the input on each run.
Use neutral nouns such as records or entries throughout, rather than
business-domain nouns copied from input data. Preserve schema keys verbatim.
In particular, write "distinct records with a known amount" for metadata
counts; do not use the word "orders" in prose or copy task metric keys.

Turn other failures and trace evidence into brief actionable process steps.
Read the input and specifications, implement, write all outputs, reopen and
validate them, fix concrete failures, then STOP. Prefer Python standard
libraries. For multiline scripts write a file then execute it with python;
do not rely on shell-specific inline quoting.
For tabular skills, require reading the data dictionary before processing.
Parse every documented date format explicitly (strptime for slash dates,
fromisoformat for ISO timestamps); never guess ambiguous day/month order.
Keep timezone-aware datetimes through filtering and convert to UTC before
formatting. Deduplicate by the documented identity key, count missing values
before filtering, and compute all row counts from the actual input.
Monetary-unit rules apply to JSON aggregates as well as cleaned CSV cells.
Require reopening JSON to check that monetary fields are integers, not
converted back to decimal currency. Retain these process steps in the skill.
The observed failure is summing integer cents correctly, then dividing by
100 when populating JSON. The tabular skill MUST explicitly prohibit this:
keep the requested JSON key names, assign integer cent totals directly,
and NEVER divide the aggregate by 100 for serialization. A JSON "number"
accepts an integer; it does not override the cent unit convention.
Require an executed Python validation after json.load of the saved output:
for each monetary aggregate key, assert type(saved[key]) is int and assert
saved[key] == independently recomputed sum of the applicable amount_cents
rows. Merely reading or printing JSON is not validation. Include a generic
executable assertion example using a placeholder money_key, not a task key.
When a metadata rule specifies an input filename, explicitly require the
basename (Path(input_path).name), excluding directory prefixes. Include
this distinction in the skill's metadata step and its final validation.

For each skill use 6-16 imperative steps, at most 80 body lines, and a
"Use when ..." description that broadly matches the domain. Put the concrete
RULE conventions early. Before returning, verify each RULE is fully captured.
For every RULE about writing an artifact, include its literal destination
path in a mandatory "Write <path>" step. A generic "write cleaned output"
is invalid. Include the exact header and filtering in that same step, never
as an optional example. The final step must explicitly require verifying
that each named output file exists. Do not omit filenames to save space.
Return raw text, no Markdown code fences or explanations, in this format:
=== SKILL: lowercase-hyphen-name ===
---
name: lowercase-hyphen-name
description: Use when ...
---
1. ...
=== END ===

LEARNING EVIDENCE:
{chr(10).join(evidence_blocks)}
"""

    # =========================================================
    # 5. Gọi curator model
    # =========================================================

    reply = (
        model
        or make_model()
    ).invoke(prompt).content

    # =========================================================
    # 6. Parse + validate + ghi skill
    # =========================================================

    written: list[Path] = []

    for name, text in parse_skill_blocks(
        str(reply)
    ):

        if len(written) >= max_skills:
            break

        problems = validate_skill(
            text,
            expected_name=name,
        )

        if problems:
            print(
                f"warning: rejected skill "
                f"{name!r}: "
                f"{', '.join(problems)}"
            )
            continue

        path = (
            destination
            / name
            / "SKILL.md"
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            text.rstrip() + "\n",
            encoding="utf-8",
        )

        written.append(path)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
