from __future__ import annotations

from pathlib import Path
from typing import TypedDict
from urllib.parse import unquote

from runtime.hashing import sha256_text


class KnowledgeFileInfo(TypedDict):
    path: str
    preview: str
    bytes: int
    sha256: str


def _safe_markdown_path(root: Path, requested_path: str) -> Path:
    decoded_path = unquote(requested_path)
    requested = Path(decoded_path)
    if requested.is_absolute():
        raise ValueError("Absolute paths are not allowed")
    if requested.suffix.lower() != ".md":
        raise ValueError("Only Markdown files may be read")
    root_resolved = root.resolve()
    candidate = (root_resolved / requested).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise ValueError("Path traversal is not allowed")
    return candidate


def list_knowledge_files(root: Path) -> list[KnowledgeFileInfo]:
    root_resolved = root.resolve()
    if not root_resolved.exists():
        return []
    files: list[KnowledgeFileInfo] = []
    for path in sorted(root_resolved.rglob("*.md")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root_resolved).as_posix()
        preview = " ".join(text.split())[:240]
        files.append(
            {
                "path": rel,
                "preview": preview,
                "bytes": len(text.encode("utf-8")),
                "sha256": sha256_text(text),
            }
        )
    return files


def build_knowledge_index(root: Path) -> tuple[str, list[KnowledgeFileInfo]]:
    files = list_knowledge_files(root)
    if not files:
        return "No Markdown knowledge files found.", files
    lines = []
    for info in files:
        lines.append(
            f"- {info['path']} ({info['bytes']} bytes, sha256={info['sha256']}): {info['preview']}"
        )
    return "\n".join(lines), files


def read_knowledge_file(root: Path, requested_path: str, max_bytes: int) -> str:
    path = _safe_markdown_path(root, requested_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Knowledge file not found: {requested_path}")
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Knowledge file exceeds max size: {size} > {max_bytes}")
    return path.read_text(encoding="utf-8")
