"""Onde a plataforma guarda log de eventos, estado da tarefa e recibos.

Tudo fica em `.agentic/` dentro do projeto (ou em AGENTIC_DIR), em arquivos simples:
dá pra auditar com `cat` e versionar se quiser.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def pasta(cwd: str | None = None) -> Path:
    base = os.environ.get("AGENTIC_DIR")
    p = Path(base) if base else Path(cwd or os.getcwd()) / ".agentic"
    p.mkdir(parents=True, exist_ok=True)
    return p


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ler_json(caminho: Path, padrao=None):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def gravar_json(caminho: Path, dados) -> None:
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def eventos(cwd: str | None = None) -> list[dict]:
    arq = pasta(cwd) / "eventos.jsonl"
    if not arq.exists():
        return []
    saida = []
    for linha in arq.read_text(encoding="utf-8").splitlines():
        try:
            saida.append(json.loads(linha))
        except json.JSONDecodeError:
            continue
    return saida
