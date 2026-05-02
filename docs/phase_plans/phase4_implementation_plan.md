# docs/phase_plans/phase4_implementation_plan.md

## Role

This document is the implementation plan for Phase 4: SQLite FTS knowledge search.

Phase 4 starts from the released Phase 3 `v3.0.1` baseline recorded in `docs/baselines/version3_phase3_baseline.md`.

## Status

Phase 4 is not started.

## Objective

Replace the naive "list all Markdown files in the system prompt" retrieval strategy with a SQLite FTS index. Keep the search layer behind a `SearchBackend` interface so future backends (Postgres FTS, vector DB) can slot in without touching the agent loop.

Reference: `docs/07_future_scaling.md` § Phase 4.

---

## Trigger conditions

Phase 4 should be started when any of the following apply (from `docs/07_future_scaling.md`):

- Markdown files are too numerous for the prompt index
- Retrieval quality becomes unacceptable (agent picks wrong files)
- Latency from full-file scanning becomes a problem
- Multiple knowledge domains need isolated indexes

---

## Scope

### New capabilities

- `SearchBackend` Protocol and `SearchResult` TypedDict in `runtime/search_backend.py`
- `SqliteFtsBackend` in `runtime/fts_backend.py` — builds an FTS5 index from `knowledge/*.md` files at startup; ranks results by relevance score
- `NaiveBackend` in `runtime/naive_backend.py` — wraps the existing `knowledge_loader.py` logic for `search_backend: naive` config
- Modified `build_knowledge_index()` in `runtime/knowledge_loader.py` — accepts a `SearchBackend`, uses `get_all()` (naive) or `search(query, top_n)` (FTS) instead of raw file scan
- New `search_knowledge` tool — lets the agent search by keyword before deciding which file to read
- Config additions: `knowledge.search_backend`, `knowledge.index_top_n`, `knowledge.fts_db_path`

### Out of scope in Phase 4

- Postgres FTS (Phase 4 ships SQLite FTS only)
- Vector DB or semantic search
- Multi-domain search isolation
- HTTP API changes, Web UI, LangGraph, write SQL tools

---

## SearchBackend interface

```python
# runtime/search_backend.py

class SearchResult(TypedDict):
    path: str        # relative path under knowledge/
    preview: str     # first N characters of content
    score: float     # relevance score (1.0 for naive, FTS rank for fts)
    sha256: str      # content hash for input_hash stability
    bytes: int       # file size

class SearchBackend(Protocol):
    def search(self, query: str, top_n: int) -> list[SearchResult]: ...
    def get_all(self) -> list[SearchResult]: ...
```

---

## New tool: `search_knowledge`

```json
{
  "name": "search_knowledge",
  "description": "Search the knowledge base by keyword. Returns ranked file names and snippets. Use this before read_knowledge_file when you are not sure which file to read.",
  "input_schema": {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"]
  }
}
```

`read_knowledge_file` tool is unchanged.

---

## Config additions (`config/app.yml`)

```yaml
knowledge:
  max_file_read_bytes: 200000
  search_backend: "naive"        # "naive" | "sqlite_fts"
  index_top_n: 10                # max files shown in system prompt knowledge index
  fts_db_path: "knowledge_index.db"  # only used when search_backend=sqlite_fts
```

`search_backend: naive` preserves current behavior. Switching to `sqlite_fts` enables FTS ranking.

---

## Completion checklist

- [ ] Step 1: Add `runtime/search_backend.py` — `SearchBackend` Protocol + `SearchResult` TypedDict.
- [ ] Step 2: Add `runtime/fts_backend.py` — `SqliteFtsBackend` (FTS5 index from `knowledge/*.md`).
- [ ] Step 3: Add `runtime/naive_backend.py` — `NaiveBackend` wrapping existing `list_knowledge_files()`.
- [ ] Step 4: Modify `runtime/knowledge_loader.py` — accept `SearchBackend`, use it in `build_knowledge_index()`.
- [ ] Step 5: Add `search_knowledge` tool to `runtime/loop.py` tool schemas and `_execute_tool()`.
- [ ] Step 6: Add `knowledge.search_backend`, `knowledge.index_top_n`, `knowledge.fts_db_path` to `config/app.yml` and validate in `runtime/config.py`.
- [ ] Step 7: Write pytest coverage — FTS indexing, search ranking, tool execution, naive fallback, input_hash stability.
- [ ] Step 8: Update `docs/CURRENT_STATE.md`, `docs/baselines/README.md`, and this file.

---

## Guardrails inherited from Phase 3

- Keep `read_knowledge_file` path safety (no absolute paths, no `..` traversal).
- `input_hash` must remain stable — search backend type and index content hash must feed into `input_hash`.
- Keep provider test doubles as the default test path (no live LLM calls required).
- Keep redaction before LLM input and trace persistence.
- Do not add write SQL tools or unrestricted SQL execution.
- `search_backend: naive` must preserve identical behavior to Phase 3.

---

## Implementation Result

**Status:** Pending

**Implemented files:**
- (To be filled on completion)

**Deviations from plan:**
- (To be filled on completion)
