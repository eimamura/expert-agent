# docs/baselines/version4_phase4_baseline.md

## Role

This is the Phase 4 completion baseline. It records the stable state released as `v4.0.0`.

## What was delivered

Phase 4 added a pluggable `SearchBackend` abstraction over the knowledge retrieval layer.

### New files

| File | Purpose |
| --- | --- |
| `runtime/search_backend.py` | `SearchBackend` Protocol + `SearchResult` TypedDict |
| `runtime/naive_backend.py` | `NaiveBackend` — keyword filter over all Markdown files |
| `runtime/fts_backend.py` | `SqliteFtsBackend` — FTS5 index built from `knowledge/*.md` |
| `tests/test_search_backend.py` | 16 tests: indexing, ranking, fallback, input_hash stability |

### Modified files

| File | Change |
| --- | --- |
| `runtime/knowledge_loader.py` | `build_knowledge_index()` accepts optional `SearchBackend` + `top_n`; added `search_knowledge_files()` |
| `runtime/loop.py` | Added `search_knowledge` tool schema; `run_agent` creates backend from config; backend threaded into `_execute_tool` |
| `runtime/config.py` | Validates `knowledge.search_backend` and `knowledge.index_top_n` |
| `config/app.yml` | Added `search_backend: naive`, `index_top_n: 10`, `fts_db_path: knowledge_index.db` |

## Behavior

- Default: `search_backend: naive` — identical behavior to Phase 3 (all Markdown files listed in system prompt)
- `search_backend: sqlite_fts` — FTS5 index built at startup; `search_knowledge` tool returns ranked results
- Agent gets `search_knowledge` tool to search before `read_knowledge_file` when uncertain which file to read
- `input_hash` stability: search backend type and file sha256s are included via `config_snapshot`

## Test baseline

117 tests passing (excluding `test_local_sqlite_seed.py`).

## Git tag

`v4.0.0`
