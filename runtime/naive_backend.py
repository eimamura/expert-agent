from __future__ import annotations

from pathlib import Path

from runtime.knowledge_loader import list_knowledge_files
from runtime.search_backend import SearchResult


class NaiveBackend:
    def __init__(self, root: Path) -> None:
        self._root = root

    def get_all(self) -> list[SearchResult]:
        files = list_knowledge_files(self._root)
        return [
            {
                "path": f["path"],
                "preview": f["preview"],
                "score": 1.0,
                "sha256": f["sha256"],
                "bytes": f["bytes"],
            }
            for f in files
        ]

    def search(self, query: str, top_n: int) -> list[SearchResult]:
        results = self.get_all()
        query_lower = query.lower()
        matched = [
            r
            for r in results
            if query_lower in r["path"].lower() or query_lower in r["preview"].lower()
        ]
        if not matched:
            matched = results
        return matched[:top_n]
