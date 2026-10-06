"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use when a task requires discovering requirements, reading documentation, "
                "docstrings, or representative data before implementation."
            ),
            "system_prompt": (
                "You are a read-only requirements explorer. Inspect the files and report exact "
                "requirements, relevant evidence, edge cases, and likely root causes. Do not edit files."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use when a task requires making focused file changes and validating them with tests or scripts."
            ),
            "system_prompt": (
                "You are an implementation specialist. Make only changes required by the delegated task, "
                "run appropriate checks, and report the files changed and actual test results."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use after changes or analysis need an independent check against requirements and edge cases."
            ),
            "system_prompt": (
                "You are a read-only reviewer. Independently inspect the result against every supplied rule, "
                "check edge cases, run non-destructive verification where useful, and report concrete findings."
            ),
        },
    ]
