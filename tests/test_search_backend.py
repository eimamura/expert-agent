from __future__ import annotations

from pathlib import Path

import pytest

from runtime.fts_backend import SqliteFtsBackend
from runtime.knowledge_loader import build_knowledge_index, search_knowledge_files
from runtime.naive_backend import NaiveBackend
from runtime.search_backend import SearchResult


def _make_knowledge(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "knowledge"
    root.mkdir()
    for name, content in files.items():
        (root / name).write_text(content, encoding="utf-8")
    return root


# ── NaiveBackend ─────────────────────────────────────────────────────────────


def test_naive_get_all_returns_all_files(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"a.md": "# A\nhello", "b.md": "# B\nworld"})
    backend = NaiveBackend(root)
    results = backend.get_all()
    paths = {r["path"] for r in results}
    assert paths == {"a.md", "b.md"}
    for r in results:
        assert r["score"] == 1.0
        assert r["sha256"]
        assert r["bytes"] > 0


def test_naive_search_matches_keyword(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"billing.md": "billing policy", "returns.md": "return window"})
    backend = NaiveBackend(root)
    results = backend.search("billing", top_n=5)
    assert len(results) == 1
    assert results[0]["path"] == "billing.md"


def test_naive_search_falls_back_to_all_when_no_match(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"a.md": "hello", "b.md": "world"})
    backend = NaiveBackend(root)
    results = backend.search("zzz_no_match", top_n=5)
    assert len(results) == 2


def test_naive_search_respects_top_n(tmp_path: Path) -> None:
    root = _make_knowledge(
        tmp_path,
        {"a.md": "billing info", "b.md": "billing details", "c.md": "billing FAQ"},
    )
    backend = NaiveBackend(root)
    results = backend.search("billing", top_n=2)
    assert len(results) == 2


def test_naive_backend_empty_root(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    backend = NaiveBackend(root)
    assert backend.get_all() == []
    assert backend.search("anything", top_n=5) == []


# ── SqliteFtsBackend ──────────────────────────────────────────────────────────


def test_fts_get_all_returns_all_files(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"a.md": "# A\nhello", "b.md": "# B\nworld"})
    db = tmp_path / "idx.db"
    backend = SqliteFtsBackend(root, db)
    results = backend.get_all()
    paths = {r["path"] for r in results}
    assert paths == {"a.md", "b.md"}


def test_fts_search_returns_ranked_results(tmp_path: Path) -> None:
    root = _make_knowledge(
        tmp_path,
        {
            "billing.md": "billing policy billing rules billing FAQ",
            "returns.md": "return window refund process",
        },
    )
    db = tmp_path / "idx.db"
    backend = SqliteFtsBackend(root, db)
    results = backend.search("billing", top_n=5)
    assert len(results) >= 1
    assert results[0]["path"] == "billing.md"
    for r in results:
        assert r["score"] >= 0


def test_fts_search_respects_top_n(tmp_path: Path) -> None:
    files = {f"doc{i}.md": f"keyword content doc {i}" for i in range(5)}
    root = _make_knowledge(tmp_path, files)
    db = tmp_path / "idx.db"
    backend = SqliteFtsBackend(root, db)
    results = backend.search("keyword", top_n=2)
    assert len(results) <= 2


def test_fts_search_malformed_query_falls_back(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"a.md": "hello world"})
    db = tmp_path / "idx.db"
    backend = SqliteFtsBackend(root, db)
    # FTS5 special characters that can cause OperationalError
    results = backend.search('"unclosed', top_n=5)
    assert isinstance(results, list)


def test_fts_sha256_stable_across_instances(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"stable.md": "fixed content"})
    db1 = tmp_path / "idx1.db"
    db2 = tmp_path / "idx2.db"
    b1 = SqliteFtsBackend(root, db1)
    b2 = SqliteFtsBackend(root, db2)
    sha1 = {r["path"]: r["sha256"] for r in b1.get_all()}
    sha2 = {r["path"]: r["sha256"] for r in b2.get_all()}
    assert sha1 == sha2


# ── build_knowledge_index integration ────────────────────────────────────────


def test_build_knowledge_index_with_naive_backend(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"guide.md": "subscription guide content"})
    backend = NaiveBackend(root)
    index_str, files = build_knowledge_index(root, backend=backend)
    assert "guide.md" in index_str
    assert len(files) == 1
    assert files[0]["score"] == 1.0


def test_build_knowledge_index_with_fts_backend(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"guide.md": "subscription guide content"})
    backend = SqliteFtsBackend(root, tmp_path / "idx.db")
    index_str, files = build_knowledge_index(root, backend=backend)
    assert "guide.md" in index_str
    assert len(files) == 1


def test_build_knowledge_index_top_n_limits_shown(tmp_path: Path) -> None:
    files = {f"doc{i}.md": f"content {i}" for i in range(5)}
    root = _make_knowledge(tmp_path, files)
    backend = NaiveBackend(root)
    index_str, all_files = build_knowledge_index(root, backend=backend, top_n=2)
    shown = [line for line in index_str.splitlines() if line.startswith("- ")]
    assert len(shown) == 2
    assert len(all_files) == 5


def test_build_knowledge_index_no_backend_fallback(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"a.md": "hello"})
    index_str, files = build_knowledge_index(root)
    assert "a.md" in index_str
    assert len(files) == 1


def test_search_knowledge_files_delegates_to_backend(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"billing.md": "billing info"})
    backend = NaiveBackend(root)
    results = search_knowledge_files(backend, "billing", top_n=5)
    assert len(results) == 1
    assert results[0]["path"] == "billing.md"


# ── input_hash stability ─────────────────────────────────────────────────────


def test_naive_backend_sha256_deterministic(tmp_path: Path) -> None:
    root = _make_knowledge(tmp_path, {"doc.md": "stable content"})
    b1 = NaiveBackend(root)
    b2 = NaiveBackend(root)
    assert b1.get_all() == b2.get_all()
