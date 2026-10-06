import json
import os
import subprocess
import sys

import pytest


@pytest.fixture(autouse=True)
def pasta_agentic(tmp_path, monkeypatch):
    """Cada teste tem sua própria .agentic/, sem tocar no repositório."""
    d = tmp_path / ".agentic"
    monkeypatch.setenv("AGENTIC_DIR", str(d))
    for var in ("ASANA_TOKEN", "SLACK_BOT_TOKEN", "GOOGLE_ACCESS_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    return d


@pytest.fixture
def rodar_hook():
    """Roda um hook do jeito que o Claude Code roda: processo separado, JSON no stdin."""

    def _rodar(modulo: str, payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", f"agentic_platform.hooks.{modulo}"],
            input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
            env={**os.environ}, timeout=30,
        )

    return _rodar
