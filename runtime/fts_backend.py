from __future__ import annotations

import sqlite3
from pathlib import Path

from runtime.knowledge_loader import list_knowledge_files
from runtime.search_backend import SearchResult


class SqliteFtsBackend:
    def __init__(self, root: Path, db_path: Path) -> None:
        self._root = root
        self._db_path = db_path
        self._files = list_knowledge_files(root)
        self._build_index()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db_path))

    def _build_index(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts "
                "USING fts5(path UNINDEXED, content, sha256 UNINDEXED, file_bytes UNINDEXED)"
            )
            conn.execute("DELETE FROM knowledge_fts")
            for f in self._files:
                full_text = (self._root / f["path"]).read_text(encoding="utf-8")
                conn.execute(
                    "INSERT INTO knowledge_fts(path, content, sha256, file_bytes) VALUES (?, ?, ?, ?)",
                    (f["path"], full_text, f["sha256"], str(f["bytes"])),
                )
            conn.commit()
        finally:
            conn.close()

    def get_all(self) -> list[SearchResult]:
        return [
            {
                "path": f["path"],
                "preview": f["preview"],
                "score": 1.0,
                "sha256": f["sha256"],
                "bytes": f["bytes"],
            }
            for f in self._files
        ]

    def search(self, query: str, top_n: int) -> list[SearchResult]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT path, snippet(knowledge_fts, 1, '', '', '...', 20), sha256, file_bytes, rank "
                "FROM knowledge_fts WHERE knowledge_fts MATCH ? ORDER BY rank LIMIT ?",
                (query, top_n),
            ).fetchall()
        except sqlite3.OperationalError:
            return self.get_all()[:top_n]
        finally:
            conn.close()

        return [
            {
                "path": row[0],
                "preview": row[1],
                "score": -row[4],
                "sha256": row[2],
                "bytes": int(row[3]),
            }
            for row in rows
        ]
