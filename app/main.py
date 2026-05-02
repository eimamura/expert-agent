from __future__ import annotations

import argparse
import sys

from runtime.config import load_config
from runtime.loop import run_agent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Phase 1 expert agent.")
    parser.add_argument("question", help="Question for the expert agent")
    parser.add_argument("--config", default="config/app.yml", help="Path to app YAML config")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    state = run_agent(args.question, config)
    print(state.final_answer)
    return 0 if state.final_status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
