# ADR-0004: Markdown-First Knowledge Base

## Status

Accepted

## Context

The agent needs access to curated domain knowledge (product definitions, business rules, policies). The options considered were: a vector database with semantic search, a full-text search index, or plain Markdown files read directly by the agent.

## Decision

Use plain Markdown files under `domains/[domain_name]/knowledge/` as the primary knowledge source for Phases 1–3. The agent reads files directly via the `read_knowledge_file` tool after inspecting a knowledge index built at run start.

## Rationale

For the MVP knowledge base size, Markdown has decisive advantages:

- **Human-editable**: Domain experts can update knowledge without touching infrastructure
- **Git-native**: Diffs are readable; history is auditable
- **No infrastructure**: No embedding pipeline, no vector DB, no index synchronization
- **Agent-readable**: Files are text the LLM can parse directly without retrieval abstractions
- **Cacheable**: Knowledge file hashes feed into `input_hash` for run-condition tracking

Semantic search becomes valuable only when the knowledge base is too large for the agent to index in the prompt, or when retrieval quality degrades. Neither condition applies in Phase 1–3.

## Consequences

**Positive**

- Zero retrieval infrastructure to operate or debug
- Knowledge updates are a Git commit, not an embedding pipeline run
- The naive retrieval strategy is easy to replace (the tool interface is stable)

**Negative**

- At large scale (hundreds of files), the knowledge index summary will hit token limits
- The agent must request files explicitly; it cannot find related content by semantic similarity

## Migration trigger

Revisit this decision (Phase 4) when:

- Markdown files are too numerous for the prompt index
- Retrieval quality becomes unacceptable
- Latency from large file reads becomes a problem

## References

- `docs/01_architecture_principles.md` — Why Markdown first
- `docs/07_future_scaling.md` § Phase 4 — External search plan
- `runtime/loop.py` — knowledge index construction
- `tools/knowledge.py` — `read_knowledge_file` implementation
