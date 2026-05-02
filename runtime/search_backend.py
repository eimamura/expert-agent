from __future__ import annotations

from typing import Protocol, TypedDict


class SearchResult(TypedDict):
    path: str
    preview: str
    score: float
    sha256: str
    bytes: int


class SearchBackend(Protocol):
    def search(self, query: str, top_n: int) -> list[SearchResult]: ...
    def get_all(self) -> list[SearchResult]: ...
