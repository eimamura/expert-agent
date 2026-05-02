from __future__ import annotations


REQUIRED_SECTIONS = [
    "Summary",
    "Findings",
    "Evidence",
    "SQL / Tool Calls Used",
    "Risks / Uncertainty",
    "Recommended Next Actions",
]


def missing_sections(text: str) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if f"## {section}" not in text]


def ensure_response_format(text: str) -> str:
    missing = missing_sections(text)
    if not missing:
        return text
    stripped = text.strip()
    sections = {
        "Summary": stripped or "No final answer was produced.",
        "Findings": "No additional findings were produced.",
        "Evidence": "No evidence was provided.",
        "SQL / Tool Calls Used": "None.",
        "Risks / Uncertainty": "The answer may be incomplete because required sections were missing from the model response.",
        "Recommended Next Actions": "Review the trace and rerun with more specific evidence requirements.",
    }
    return "\n\n".join(f"## {section}\n{sections[section]}" for section in REQUIRED_SECTIONS)
