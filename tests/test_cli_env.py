from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import app.main as cli


def test_load_dotenv_sets_missing_values_without_overwriting(tmp_path: Path, monkeypatch: Any) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        """
        # Local values
        ANTHROPIC_API_KEY=from-file
        DATABASE_URL="sqlite:///./data/local.sqlite"
        EXISTING=from-file
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("EXISTING", "from-env")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    cli.load_dotenv(env_path)

    assert os.environ["ANTHROPIC_API_KEY"] == "from-file"
    assert os.environ["DATABASE_URL"] == "sqlite:///./data/local.sqlite"
    assert os.environ["EXISTING"] == "from-env"


def test_main_loads_dotenv_before_running_agent(tmp_path: Path, monkeypatch: Any) -> None:
    config_path = Path(__file__).parents[1] / "config" / "app.yml"
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fake_run_agent(question: str, config: dict[str, Any]) -> SimpleNamespace:
        assert question == "What should I investigate first?"
        assert config["llm"]["provider"] == "anthropic"
        assert os.environ["ANTHROPIC_API_KEY"] == "from-file"
        return SimpleNamespace(final_answer="ok", final_status="success")

    monkeypatch.setattr(cli, "run_agent", fake_run_agent)

    assert cli.main(["--config", str(config_path), "What should I investigate first?"]) == 0
