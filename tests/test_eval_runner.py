from __future__ import annotations

import json
from pathlib import Path

from runtime.formatter import REQUIRED_SECTIONS
from runtime.config import domain_path, load_config
from runtime.redaction import redact_text
from runtime.trace_reader import load_validated_trace
from runtime.eval_assertions import assert_trace_case
from tools.sql import extract_tables, validate_readonly_sql


ALLOWED = {"main.customers", "main.orders", "main.order_items", "main.products"}
CONFIG = load_config()
EVAL_ROOT = domain_path(CONFIG, "evals")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_seed_and_domain_eval_cases_have_required_fields() -> None:
    for path in [EVAL_ROOT / "seed_questions.jsonl", EVAL_ROOT / "domain_cases.jsonl"]:
        cases = load_jsonl(path)
        assert cases
        for case in cases:
            assert case["id"]
            assert case["question"]
            assert isinstance(case.get("expected_tools", []), list)
            assert isinstance(case.get("expected_response_sections", []), list)


def test_sql_safety_eval_cases_are_deterministic() -> None:
    cases = load_jsonl(EVAL_ROOT / "sql_safety_cases.jsonl")
    assert cases
    for case in cases:
        dialects = case.get("dialects") or ["sqlite"]
        for dialect in dialects:
            if case["allowed"]:
                validate_readonly_sql(case["query"], dialect, ALLOWED)
                if "expected_tables" in case:
                    assert sorted(extract_tables(case["query"], dialect)) == sorted(case["expected_tables"])
            else:
                try:
                    validate_readonly_sql(case["query"], dialect, ALLOWED)
                except ValueError:
                    pass
                else:
                    raise AssertionError(f"Expected SQL case to be rejected: {case['id']}")


def test_response_format_eval_cases_reference_required_sections() -> None:
    cases = load_jsonl(EVAL_ROOT / "response_format_cases.jsonl")
    assert cases
    for case in cases:
        assert case["required_sections"] == REQUIRED_SECTIONS


def test_redaction_eval_cases_are_deterministic() -> None:
    cases = load_jsonl(EVAL_ROOT / "redaction_cases.jsonl")
    assert cases
    for case in cases:
        output = redact_text(case["input"])
        for marker in case["forbidden_output_markers"]:
            assert marker not in output
        for marker in case["required_output_markers"]:
            assert marker in output


def test_runtime_limit_eval_cases_have_required_fields() -> None:
    cases = load_jsonl(EVAL_ROOT / "runtime_limit_cases.jsonl")
    assert cases
    for case in cases:
        assert case["expected_terminal_status"]
        assert isinstance(case["required_limit_metadata"], list)


def test_trace_based_eval_assertions_on_fixture() -> None:
    events = load_validated_trace("fixtures/traces/success_basic.jsonl")
    assert_trace_case(
        events,
        {
            "expected_tools": ["read_knowledge_file"],
            "forbidden_tools": ["execute_any_sql", "run_write_sql"],
            "tools_call_order": ["read_knowledge_file"],
            "expected_terminal_status": "success",
            "forbidden_output_markers": ["jane@example.com"],
        },
    )
