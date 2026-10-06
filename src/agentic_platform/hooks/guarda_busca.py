"""Bloqueia busca a partir da raiz do disco (PreToolUse em Bash, PowerShell, Grep e Glob).

Medido em produção: 46 de 52 buscas na raiz vinham de subagentes, com até 124 s cada.
Responde com permissionDecision "deny" no JSON, e o modelo recebe o motivo e refaz a
busca no escopo certo. Não usa exit code 2: no Windows o Claude Code tratou o exit 2
como erro não bloqueante e executou o comando mesmo assim (visto num teste real).
"""
from __future__ import annotations

import json
import re

from agentic_platform.hooks import ler_payload

RAIZ_WINDOWS = r"[A-Za-z]:[\\/]?"
RAIZES = re.compile(r"""(?:^|\s)["']?(?:/|""" + RAIZ_WINDOWS + r"""|~)["']?(?:\s|$)""")
CMD_BUSCA = re.compile(
    r"\b(?:find|grep\s+-[a-zA-Z]*r[a-zA-Z]*|rg|fd|locate|du"
    r"|(?:Get-ChildItem|gci|ls|dir)\b[^|;]*\s-r(?:ecurse)?|dir\s+/s)\b",
    re.IGNORECASE,
)
SHELLS = ("Bash", "PowerShell")


def motivo_bloqueio(payload: dict) -> str | None:
    ferramenta = payload.get("tool_name")
    entrada = payload.get("tool_input") or {}
    if ferramenta in SHELLS:
        cmd = entrada.get("command", "")
        if CMD_BUSCA.search(cmd) and RAIZES.search(" " + cmd + " "):
            return f"busca na raiz do disco: {cmd[:120]}"
    elif ferramenta in ("Grep", "Glob"):
        caminho = (entrada.get("path") or "").strip()
        if caminho in ("/", "~") or re.fullmatch(RAIZ_WINDOWS, caminho):
            return f"{ferramenta} com path={caminho!r}"
    return None


def decidir(payload: dict) -> dict | None:
    motivo = motivo_bloqueio(payload)
    if not motivo:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"Bloqueado ({motivo}). Busque dentro do repositório ou da pasta da demanda; "
            "varrer o disco inteiro custa minutos e não acha nada útil."
        ),
    }}


def main() -> None:
    saida = decidir(ler_payload())
    if saida:
        print(json.dumps(saida, ensure_ascii=False))


if __name__ == "__main__":
    main()
