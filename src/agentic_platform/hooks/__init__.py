"""Hooks do Claude Code. Cada módulo lê o payload JSON do stdin e responde pelo protocolo de hooks."""
import json
import sys


def ler_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
