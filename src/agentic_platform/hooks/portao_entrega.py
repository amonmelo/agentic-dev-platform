"""Portão de entrega (hook Stop): o agente não declara "pronto" sem recibo de validação.

Medido em produção: o recibo era pulado em 26 de 39 rodadas que editaram código.
Regra: se a sessão editou arquivo depois do último recibo aprovado, o Stop é bloqueado
e o modelo recebe o motivo. O recibo é gerado pela skill /validar-entrega (`agentic-recibo`).
"""
from __future__ import annotations

import json

from agentic_platform import estado
from agentic_platform.hooks import ler_payload

EDICAO = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def decidir(payload: dict) -> dict | None:
    if payload.get("stop_hook_active"):
        return None  # já bloqueou uma vez nesta parada; não entra em loop
    sessao = payload.get("session_id")
    cwd = payload.get("cwd")
    edicoes = [
        e["ts"] for e in estado.eventos(cwd)
        if e.get("sessao") == sessao and e.get("ferramenta") in EDICAO and e.get("evento") == "PostToolUse" and not e.get("falhou")
    ]
    if not edicoes:
        return None
    recibo = estado.ler_json(estado.pasta(cwd) / "recibo.json", {}) or {}
    if recibo.get("aprovado") and recibo.get("criado_em", "") >= max(edicoes):
        return None
    return {
        "decision": "block",
        "reason": (
            "Você editou código e não há recibo de validação depois da última edição. "
            "Rode /validar-entrega (baseline × candidato com teste real) e gere o recibo "
            "com `agentic-recibo --aprovado --evidencia ...` antes de encerrar."
        ),
    }


def main() -> None:
    saida = decidir(ler_payload())
    if saida:
        print(json.dumps(saida, ensure_ascii=False))


if __name__ == "__main__":
    main()
