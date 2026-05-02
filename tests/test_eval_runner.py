from __future__ import annotations

import json
from pathlib import Path

from runtime.formatter import REQUIRED_SECTIONS
from tools.sql import extract_tables, validate_readonly_sql


ALLOWED = {"main.customers", "main.orders", "main.order_items", "main.products"}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_seed_and_domain_eval_cases_have_required_fields() -> None:
    for path in [Path("evals/seed_questions.jsonl"), Path("evals/domain_cases.jsonl")]:
        cases = load_jsonl(path)
        assert cases
        for case in cases:
            assert case["id"]
            assert case["question"]
            assert isinstance(case.get("expected_tools", []), list)
            assert isinstance(case.get("expected_response_sections", []), list)


def test_sql_safety_eval_cases_are_deterministic() -> None:
    cases = load_jsonl(Path("evals/sql_safety_cases.jsonl"))
    assert cases
    for case in cases:
        if case["allowed"]:
            validate_readonly_sql(case["query"], "sqlite", ALLOWED)
            if "expected_tables" in case:
                assert sorted(extract_tables(case["query"], "sqlite")) == sorted(case["expected_tables"])
        else:
            try:
                validate_readonly_sql(case["query"], "sqlite", ALLOWED)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Expected SQL case to be rejected: {case['id']}")


def test_response_format_eval_cases_reference_required_sections() -> None:
    cases = load_jsonl(Path("evals/response_format_cases.jsonl"))
    assert cases
    for case in cases:
        assert case["required_sections"] == REQUIRED_SECTIONS
