"""Grava cada ferramenta, subagente, falha e compactação em .agentic/eventos.jsonl.

É a base de tudo: sem log não dá pra saber onde o agente erra. Os outros hooks e o
`agentic-metricas` leem este arquivo.
"""
from __future__ import annotations

import json

from agentic_platform import estado
from agentic_platform.hooks import ler_payload


def registrar(payload: dict) -> dict:
    tool_input = payload.get("tool_input") or {}
    resposta = payload.get("tool_response")
    falhou = payload.get("hook_event_name") == "PostToolUseFailure" or (
        isinstance(resposta, dict) and bool(resposta.get("is_error") or resposta.get("error"))
    )
    evento = {
        "ts": estado.agora(),
        "sessao": payload.get("session_id", "?"),
        "evento": payload.get("hook_event_name", "?"),
        "ferramenta": payload.get("tool_name"),
        "agente": payload.get("agent_type") or "principal",
        "alvo": tool_input.get("file_path") or tool_input.get("command") or tool_input.get("pattern"),
        "falhou": bool(falhou),
    }
    arq = estado.pasta(payload.get("cwd")) / "eventos.jsonl"
    with arq.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return evento


def main() -> None:
    registrar(ler_payload())


if __name__ == "__main__":
    main()
