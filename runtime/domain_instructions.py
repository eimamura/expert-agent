from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from runtime.hashing import sha256_text


InstructionKind = Literal["skills", "policies"]


class DomainInstructionFile(TypedDict):
    kind: InstructionKind
    path: str
    content: str
    bytes: int
    sha256: str


def _list_markdown_files(
    domain_root: Path,
    directory: InstructionKind,
) -> list[DomainInstructionFile]:
    root_resolved = domain_root.resolve()
    instruction_dir = root_resolved / directory
    if not instruction_dir.exists():
        return []
    files: list[DomainInstructionFile] = []
    for path in sorted(instruction_dir.glob("*.md")):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        rel = path.relative_to(root_resolved).as_posix()
        files.append(
            {
                "kind": directory,
                "path": rel,
                "content": content,
                "bytes": len(content.encode("utf-8")),
                "sha256": sha256_text(content),
            }
        )
    return files


def load_domain_instruction_files(domain_root: Path) -> list[DomainInstructionFile]:
    return [
        *_list_markdown_files(domain_root, "skills"),
        *_list_markdown_files(domain_root, "policies"),
    ]


def render_domain_instructions(files: list[DomainInstructionFile]) -> str:
    sections: list[str] = []
    for kind, title in (("skills", "Domain Skills"), ("policies", "Domain Policies")):
        matching = [item for item in files if item["kind"] == kind]
        sections.append(f"## {title}")
        if not matching:
            sections.append("No Markdown files found.")
            continue
        for item in matching:
            sections.append(f"### {item['path']}")
            sections.append(item["content"].strip())
    return "\n\n".join(sections)
