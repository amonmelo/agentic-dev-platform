---
name: code-review
description: Revisa um diff em três níveis (crítico, importante, melhoria), confirma cada achado com o cético e detecta "diff fantasma" (arquivo alterado sem relação com a demanda). Use antes de abrir MR ou quando pedirem revisão.
---

# /code-review

## Passos
1. Pegue o diff real: `git diff <base>...HEAD`. Revise só o que mudou.
2. **Diff fantasma:** liste arquivos alterados que não têm relação com a demanda (formatação em massa, debug esquecido, lockfile). Cada um vira achado.
3. Classifique cada achado:
   - **Crítico:** quebra comportamento, perde dado, expõe segredo, falha de segurança.
   - **Importante:** bug provável, caso de borda sem tratamento, teste faltando para o caso da demanda.
   - **Melhoria:** legibilidade, duplicação, nome.
4. Mande cada achado crítico ou importante para o subagente **cético**. Ele tenta refutar. Só fica o que sobreviver.
5. Saída em `.agentic/review.md`: `nível | arquivo:linha | o problema | cenário que quebra | sugestão`.

## Regras
- Achado sem cenário concreto de falha não é crítico.
- Não reescreva o código do autor no review. Aponte e sugira o menor ajuste.
- Crítico encontrado = a entrega volta para `/investigar`, mesmo com teste verde.
