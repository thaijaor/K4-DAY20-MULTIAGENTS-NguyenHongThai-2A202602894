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
            "description": "Call before implementing when requirements, code contracts, or input formats need investigation.",
            "system_prompt": (
                "You investigate only the delegated question. Read relevant documentation, "
                "docstrings, code and data samples without changing files. Report facts with "
                "file references, ambiguities and suggested next steps. Do not implement fixes."
            ),
        },
        {
            "name": "implementer",
            "description": "Call when a concrete code fix or data transformation is specified and needs implementation and verification.",
            "system_prompt": (
                "Implement only the delegated change under the supplied rules. Inspect relevant "
                "inputs, make focused edits, and run applicable tests or validation scripts. "
                "Never modify skills. Return changed paths, validation results and unresolved issues."
            ),
        },
        {
            "name": "reviewer",
            "description": "Call after implementation to independently check outputs against requirements and edge cases before accepting them.",
            "system_prompt": (
                "Review only the delegated outputs against the supplied requirements. Inspect "
                "files and run non-destructive checks for edge cases and consistency. Do not "
                "edit files. Return specific findings with evidence and any missing verification."
            ),
        },
    ]
