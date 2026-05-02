from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from runtime.config import load_config
from runtime.trace_reader import assert_trace_replayable
from runtime.trace_summary import summarize_trace
from runtime.loop import run_agent


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv and argv[0] == "trace-summary":
        parser = argparse.ArgumentParser(description="Summarize a JSONL trace.")
        parser.add_argument("command")
        parser.add_argument("trace_path")
        args = parser.parse_args(argv)
        print(json.dumps(summarize_trace(args.trace_path), sort_keys=True))
        return 0
    if argv and argv[0] == "eval":
        parser = argparse.ArgumentParser(description="Run deterministic local eval validation.")
        parser.add_argument("command")
        parser.add_argument("--fixtures", default="fixtures/traces", help="Trace fixture directory")
        args = parser.parse_args(argv)
        fixture_dir = Path(args.fixtures)
        for path in sorted(fixture_dir.glob("*.jsonl")):
            assert_trace_replayable(path)
        print(json.dumps({"status": "success", "trace_fixtures_checked": len(list(fixture_dir.glob("*.jsonl")))}, sort_keys=True))
        return 0

    parser = argparse.ArgumentParser(description="Run the local Phase 1 expert agent.")
    parser.add_argument("question", help="Question for the expert agent")
    parser.add_argument("--config", default="config/app.yml", help="Path to app YAML config")
    args = parser.parse_args(argv)

    load_dotenv()
    config = load_config(args.config)
    state = run_agent(args.question, config)
    print(state.final_answer)
    return 0 if state.final_status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
