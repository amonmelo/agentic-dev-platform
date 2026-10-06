"""Gera um log sintético com as proporções medidas na versão interna e roda as métricas.

    python examples/log_demo.py

Os dados são sintéticos. Só as proporções vêm da medição real:
26 de 39 sessões que editaram código terminaram sem recibo; 46 de 52 buscas na raiz
vieram de subagentes. O resto é o mínimo pra montar sessões plausíveis.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SESSOES = 39
SEM_RECIBO = 26
BUSCAS_RAIZ_SUB = 46
BUSCAS_RAIZ_PRINCIPAL = 6


def ev(sessao: int, evento: str, ferramenta: str, alvo: str = "", agente: str = "principal") -> dict:
    return {"ts": "2026-10-01T12:00:00+00:00", "sessao": f"s{sessao:02d}", "evento": evento,
            "ferramenta": ferramenta, "agente": agente, "alvo": alvo, "falhou": False}


def gerar() -> list[dict]:
    eventos = []
    for s in range(SESSOES):
        eventos += [
            ev(s, "PostToolUse", "Read", "src/app/service.py"),
            ev(s, "SubagentStop", "Task", agente="investigador"),
            ev(s, "SubagentStop", "Task", agente="cetico"),
            ev(s, "PostToolUse", "Edit", "src/app/service.py"),
            ev(s, "PostToolUse", "Bash", "pytest -q"),
        ]
        if s >= SEM_RECIBO:
            eventos.append(ev(s, "PostToolUse", "Bash", "agentic-recibo --aprovado --evidencia 'pytest: ok'"))
    for i in range(BUSCAS_RAIZ_SUB):
        eventos.append(ev(i % SESSOES, "PreToolUse", "Bash", "find / -name settings.py", agente="investigador"))
    for i in range(BUSCAS_RAIZ_PRINCIPAL):
        eventos.append(ev(i, "PreToolUse", "Bash", "grep -rn DATABASE_URL /"))
    return eventos


def main() -> None:
    pasta = Path(tempfile.mkdtemp()) / ".agentic"
    pasta.mkdir()
    with (pasta / "eventos.jsonl").open("w", encoding="utf-8") as f:
        for e in gerar():
            f.write(json.dumps(e) + "\n")
    subprocess.run([sys.executable, "-m", "agentic_platform.metricas"], env={**os.environ, "AGENTIC_DIR": str(pasta)},
                   check=True)


if __name__ == "__main__":
    main()
