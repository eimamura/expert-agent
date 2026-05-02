# docs/00_project_overview.md

## Role

This document defines the project goal, vocabulary, recommended stack, and target repository structure.

## Read first

- `../SPEC.md`

## Related documents

- `docs/01_architecture_principles.md`
- `docs/02_phase1_mvp_scope.md`

---

# AI Domain Expert Agent MVP

## Goal

Build a domain expert AI agent foundation that can start as a local-first workflow.

The initial system uses Markdown as the primary format for knowledge, procedures, policies, and decision criteria. It must be able to grow later into a Web/API service, external search system, LangGraph workflow, multi-channel assistant, and eventually an agent platform.

## Scaling roadmap

```text
Phase 0: Markdown design and expected-question mapping
Phase 1: Local minimal agent loop
Phase 2: Trace, eval, and runtime refinement
Phase 3: Web/API layer
Phase 4: External search infrastructure
Phase 5: LangGraph / workflow orchestration
Phase 6: Multiple channels
Phase 7: Agent platform
```

## Vocabulary

| Term | Meaning |
| --- | --- |
| Minimal agent loop | The smallest loop that calls an LLM, executes tool calls, appends tool results, and calls the LLM again. |
| Read-only DB user | A database user that has only SELECT permissions. |
| Read-only SQL | A single SELECT query that passes parser-backed validation. |
| Trace | A record of LLM calls, tool calls, results, token usage, and cost for an agent run. |
| Redaction | Masking secrets or personally identifiable information before saving traces or sending data to the LLM. |
| `input_hash` | A hash used to identify whether run conditions are the same for replay or comparison. |
| Model alias | An abstract model name such as `sonnet_latest`, resolved to a concrete provider model id at runtime. |

## Python requirement

```toml
requires-python = ">=3.10"
```

Reasons:

- `Path.is_relative_to()` can be used safely.
- Modern type hints, Pydantic, and provider SDKs are better supported.

## Dependency management

Required:

- Use `uv`.
- Commit the lock file.
- Pin SDK and LangChain-family package versions if such packages are introduced.

Recommended setup:

```bash
uv init
uv add "anthropic" "openai" "sqlglot>=25.0" "pydantic" "pyyaml" "pytest" "ulid-py"
uv lock
```

## Version floors

| Package | Minimum | Reason |
| --- | --- | --- |
| Python | >=3.10 | Path handling, type hints, Pydantic, and SDK compatibility. |
| sqlglot | >=25.0 | The spec assumes `Expression.walk()` yields expressions directly. |

## Recommended MVP stack

| Area | Recommendation | Reason |
| --- | --- | --- |
| Language | Python 3.10+ | Good fit for LLMs, data, automation, and CLI tools. |
| Agent loop | Custom minimal loop | Keeps behavior understandable and controllable in the MVP. |
| LLM provider | Claude API or OpenAI API | Both support tool calling. |
| Config | YAML | Easy to review and version in Git. |
| Knowledge | Markdown | Readable by humans and agents. |
| Tools | Python functions | Safe wrappers around DB, file, and reporting behavior. |
| SQL validation | read-only DB user plus `sqlglot` | Avoids relying only on string blocking. |
| Eval | JSONL plus pytest | Simple, local, and automatable. |
| Trace | JSONL | Lightweight and easy to externalize later. |
| `run_id` | ULID | Sortable by time and low collision risk. |
| DB | SQLite for local MVP | Easy local development target. |
| Dependency manager | `uv` | Lock file required. |

## Recommended repository structure

```text
expert-agent/
  AGENTS.md
  CLAUDE.md
  SPEC.md
  IMPLEMENTATION_PLAN.md
  CHANGELOG.md
  pyproject.toml
  uv.lock
  .env.example

  app/
    main.py

  agents/
    expert_agent.py
    prompts.py

  runtime/
    loop.py
    state.py
    trace.py
    config.py
    cost.py
    redaction.py
    knowledge_loader.py
    hashing.py
    ids.py

  config/
    app.yml

  tools/
    __init__.py
    sql.py

  knowledge/
    domain_overview.md
    kpi_definitions.md
    database_schema.md

  skills/
    investigation_skill.md
    sql_diagnosis_skill.md
    report_generation_skill.md

  policies/
    db_safety.md
    production_change_policy.md
    response_policy.md

  rules/
    allowed_tables.yml
    thresholds.yml
    redaction.yml
    pii_columns.yml

  evals/
    seed_questions.jsonl
    domain_cases.jsonl
    sql_safety_cases.jsonl
    response_format_cases.jsonl

  traces/
    .gitkeep

  tests/
    test_sql_safety.py
    test_knowledge_loader.py
    test_redaction.py
    test_tools.py
    test_eval_runner.py
    test_response_format.py
```

## Language policy

All repository Markdown must be written in English.
Future knowledge files, policy files, prompts, and eval descriptions should also be English unless a task explicitly requires localized domain source material.
