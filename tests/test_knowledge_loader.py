from __future__ import annotations

from pathlib import Path

import pytest

from runtime.knowledge_loader import build_knowledge_index, list_knowledge_files, read_knowledge_file


def test_list_knowledge_files_markdown_only(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# A\nhello world", encoding="utf-8")
    (tmp_path / "b.txt").write_text("ignored", encoding="utf-8")
    files = list_knowledge_files(tmp_path)
    assert [item["path"] for item in files] == ["a.md"]
    assert files[0]["bytes"] > 0
    assert files[0]["sha256"]
    index, source = build_knowledge_index(tmp_path)
    assert "a.md" in index
    assert source == files


def test_read_knowledge_file_rejects_absolute_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Absolute"):
        read_knowledge_file(tmp_path, str(tmp_path / "a.md"), 100)


def test_read_knowledge_file_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="traversal"):
        read_knowledge_file(tmp_path, "../outside.md", 100)


def test_read_knowledge_file_rejects_non_markdown(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Markdown"):
        read_knowledge_file(tmp_path, "a.txt", 100)


def test_read_knowledge_file_missing_and_max_bytes(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_knowledge_file(tmp_path, "missing.md", 100)
    (tmp_path / "big.md").write_text("abcdef", encoding="utf-8")
    with pytest.raises(ValueError, match="max size"):
        read_knowledge_file(tmp_path, "big.md", 3)
