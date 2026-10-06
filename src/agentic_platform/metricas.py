"""Mede o comportamento real dos agentes e diz onde mexer.

Lê .agentic/eventos.jsonl (gravado pelo hook de observabilidade) e devolve números e
recomendações. Foi assim que os hooks deste repositório nasceram: primeiro medir,
depois criar a regra.

    agentic-metricas            # resumo + o que melhorar
    agentic-metricas --json     # para dashboard
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

from agentic_platform import estado
from agentic_platform.hooks.guarda_busca import motivo_bloqueio

EDICAO = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def calcular(eventos: list[dict]) -> dict:
    por_sessao: dict[str, list[dict]] = defaultdict(list)
    for e in eventos:
        por_sessao[e.get("sessao", "?")].append(e)

    editaram = sem_recibo = 0
    for evs in por_sessao.values():
        if any(e.get("ferramenta") in EDICAO for e in evs):
            editaram += 1
            if not any("agentic-recibo" in str(e.get("alvo") or "") for e in evs):
                sem_recibo += 1

    buscas_raiz: Counter = Counter()
    for e in eventos:
        if e.get("evento") != "PreToolUse":
            continue
        alvo = str(e.get("alvo") or "")
        if motivo_bloqueio({"tool_name": e.get("ferramenta"), "tool_input": {"command": alvo, "path": alvo}}):
            buscas_raiz[e.get("agente", "principal")] += 1

    uso = [e for e in eventos if e.get("evento") in ("PostToolUse", "PostToolUseFailure")]
    falhas = Counter(e.get("ferramenta") for e in uso if e.get("falhou"))
    return {
        "sessoes": len(por_sessao),
        "chamadas_de_ferramenta": len(uso),
        "falhas": sum(falhas.values()),
        "falhas_por_ferramenta": dict(falhas),
        "subagentes": sum(1 for e in eventos if e.get("evento") == "SubagentStop"),
        "compactacoes": sum(1 for e in eventos if e.get("evento") == "PreCompact"),
        "sessoes_que_editaram": editaram,
        "editaram_sem_recibo": sem_recibo,
        "buscas_na_raiz_por_agente": dict(buscas_raiz),
        "uso_por_ferramenta": dict(Counter(e.get("ferramenta") for e in uso).most_common(8)),
    }


def diagnosticar(m: dict) -> list[str]:
    """Transforma os números em ação. Cada regra tem um limite explícito e diz o que fazer."""
    rec: list[str] = []
    if m["sessoes_que_editaram"] and m["editaram_sem_recibo"] / m["sessoes_que_editaram"] > 0.2:
        pct = 100 * m["editaram_sem_recibo"] // m["sessoes_que_editaram"]
        rec.append(f"{pct}% das sessões que editaram código terminaram sem recibo de validação. "
                   "Confirme que o hook portao_entrega está ligado no Stop.")
    raiz = sum(m["buscas_na_raiz_por_agente"].values())
    if raiz:
        sub = raiz - m["buscas_na_raiz_por_agente"].get("principal", 0)
        rec.append(f"{raiz} buscas na raiz do disco ({sub} vindas de subagentes). "
                   "Passe o caminho do repositório no prompt do subagente e mantenha o guarda_busca ativo.")
    for ferramenta, n in m["falhas_por_ferramenta"].items():
        total = m["uso_por_ferramenta"].get(ferramenta) or n
        if n >= 3 and n / total > 0.25:
            rec.append(f"{ferramenta} falhou {n} de {total} vezes. Olhe os alvos dessas chamadas no eventos.jsonl; "
                       "geralmente é caminho errado ou comando que depende de estado.")
    if m["sessoes"] and m["compactacoes"] / m["sessoes"] > 0.5:
        rec.append("Mais da metade das sessões compactou o contexto. Grave .agentic/estado.json a cada etapa "
                   "para o hook de retomada ter o que devolver, e quebre tarefas longas em subagentes.")
    if m["sessoes_que_editaram"] and not m["subagentes"]:
        rec.append("Nenhum subagente foi usado em sessões com código. O cético não está revisando os achados.")
    return rec or ["Nada fora do esperado nos limites atuais."]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    m = calcular(estado.eventos())
    rec = diagnosticar(m)
    if a.json:
        print(json.dumps({"metricas": m, "recomendacoes": rec}, ensure_ascii=False, indent=2))
        return
    print(f"Sessões: {m['sessoes']} · chamadas: {m['chamadas_de_ferramenta']} · falhas: {m['falhas']}")
    print(f"Subagentes: {m['subagentes']} · compactações: {m['compactacoes']}")
    print(f"Editaram código: {m['sessoes_que_editaram']} · sem recibo: {m['editaram_sem_recibo']}")
    print(f"Buscas na raiz: {m['buscas_na_raiz_por_agente'] or 'nenhuma'}")
    print("\nO que melhorar:")
    for r in rec:
        print(f"- {r}")


if __name__ == "__main__":
    main()
