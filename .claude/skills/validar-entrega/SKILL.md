---
name: validar-entrega
description: Valida uma entrega comparando baseline (antes) e candidato (depois) com testes executados de verdade, e gera o recibo que libera o portão de entrega. Use antes de dizer que algo está pronto, abrir MR ou mover o card.
---

# /validar-entrega

Nada é aprovado com teste simulado ou cenário que não rodou.

## Passos
1. **Baseline:** faça checkout do commit anterior à mudança (worktree separado) e rode os casos. Anote o resultado.
2. **Candidato:** rode os mesmos casos na versão nova.
3. **Matriz:** monte `caso → baseline → candidato → evidência` em `.agentic/validacao.md`.
   - O caso do bug precisa falhar no baseline e passar no candidato.
   - Os demais casos precisam dar o mesmo resultado nos dois (regressão).
4. **E2E quando houver tela:** Playwright, gravando antes e depois. O vídeo é evidência.
5. **Code review:** rode `/code-review` no diff. Achado crítico volta pra correção.
6. **Recibo:**

```bash
agentic-recibo --aprovado \
  --evidencia "pytest tests/test_exportacao.py: 14 passed (baseline: 1 failed)" \
  --evidencia "E2E exportar NPS: .agentic/videos/antes.webm .agentic/videos/depois.webm"
```

Reprovou? `agentic-recibo --evidencia "..."` sem `--aprovado` e volte para `/investigar`.

## Por que existe
Medido em produção: o recibo era pulado em 26 de 39 rodadas que editaram código. Desde que o hook `portao_entrega` entrou, o agente não consegue encerrar sem ele.
