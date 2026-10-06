"""Retomada após compactação (SessionStart com source=compact).

Quando o contexto é resumido, o modelo esquece em que etapa estava. Este hook devolve
a etapa atual, o próximo passo e a definição de pronto gravados em .agentic/estado.json.
"""
from __future__ import annotations

import json

from agentic_platform import estado
from agentic_platform.hooks import ler_payload


def contexto(payload: dict) -> dict | None:
    if payload.get("source") not in ("compact", "resume"):
        return None
    st = estado.ler_json(estado.pasta(payload.get("cwd")) / "estado.json")
    if not st:
        return None
    texto = (
        f"Retomando a tarefa '{st.get('tarefa', '?')}'.\n"
        f"Etapa atual: {st.get('etapa', '?')}\n"
        f"Próximo passo: {st.get('proximo_passo', '?')}\n"
        f"Pronto quando: {st.get('definicao_de_pronto', '?')}"
    )
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto}}


def main() -> None:
    saida = contexto(ler_payload())
    if saida:
        print(json.dumps(saida, ensure_ascii=False))


if __name__ == "__main__":
    main()
