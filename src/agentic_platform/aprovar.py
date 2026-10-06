"""Aprovação humana dos rascunhos criados pelos agentes.

    agentic-aprovar              # lista pendentes
    agentic-aprovar 3f9a1c2e     # aprova
    agentic-aprovar 3f9a1c2e --rejeitar
"""
from __future__ import annotations

import argparse

from agentic_platform import rascunhos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id", nargs="?")
    ap.add_argument("--rejeitar", action="store_true")
    a = ap.parse_args()
    if not a.id:
        pend = rascunhos.listar("pendente")
        if not pend:
            print("Nenhum rascunho pendente.")
        for r in pend:
            print(f"[{r['id']}] {r['canal']} → {r['destino']}\n{r['texto']}\n")
        return
    r = rascunhos.mudar_status(a.id, "rejeitado" if a.rejeitar else "aprovado")
    print(f"{r['id']}: {r['status']}")


if __name__ == "__main__":
    main()
