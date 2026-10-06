r"""Gera o recibo de validação que libera o portão de entrega.

    agentic-recibo --aprovado --evidencia "pytest tests/test_pedido.py: 12 passed" \
                   --evidencia "E2E baseline x candidato: videos/antes.mp4 videos/depois.mp4"

Sem `--evidencia` o recibo não é aceito: "testei e funcionou" não é prova.
"""
from __future__ import annotations

import argparse

from agentic_platform import estado


def gerar(aprovado: bool, evidencias: list[str], cwd: str | None = None) -> dict:
    if aprovado and not evidencias:
        raise ValueError("recibo aprovado precisa de pelo menos uma evidência executada")
    recibo = {"aprovado": aprovado, "evidencias": evidencias, "criado_em": estado.agora()}
    estado.gravar_json(estado.pasta(cwd) / "recibo.json", recibo)
    return recibo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aprovado", action="store_true")
    ap.add_argument("--evidencia", action="append", default=[])
    a = ap.parse_args()
    try:
        r = gerar(a.aprovado, a.evidencia)
    except ValueError as e:
        ap.error(str(e))
    print(f"recibo gravado: aprovado={r['aprovado']} evidencias={len(r['evidencias'])}")


if __name__ == "__main__":
    main()
