from __future__ import annotations

from runtime.formatter import REQUIRED_SECTIONS, ensure_response_format, missing_sections


def test_ensure_response_format_adds_required_sections() -> None:
    formatted = ensure_response_format("plain answer")
    assert missing_sections(formatted) == []
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in formatted


def test_ensure_response_format_preserves_complete_answer() -> None:
    answer = "\n\n".join(f"## {section}\nBody" for section in REQUIRED_SECTIONS)
    assert ensure_response_format(answer) == answer
