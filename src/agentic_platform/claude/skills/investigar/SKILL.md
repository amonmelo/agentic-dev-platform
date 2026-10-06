---
name: investigar
description: Investiga um bug ou demanda de sustentação até a causa raiz, com enxame de subagentes (leitor, investigador, cético) e prova por teste real. Use quando o pedido for "investigar", "corrigir", "por que isso quebrou" ou trouxer um card/tarefa com defeito.
---

# /investigar

Leva uma demanda do card até um diff mínimo com prova. Mock não é prova.

## 0. Abrir o estado
Grave `.agentic/estado.json` antes de começar e atualize a cada etapa:

```json
{"tarefa": "<id ou título>", "etapa": "1-entender", "proximo_passo": "...",
 "definicao_de_pronto": "teste que reproduz o bug passa no candidato e falha no baseline"}
```

Se o contexto for compactado, o hook de retomada devolve isso pra você.

## 1. Entender (leitor)
- Puxe a demanda pelo MCP (`asana_listar_tarefas`, `sheets_ler`) e salve em `.agentic/demanda/`.
- Mande cada anexo, print ou resultado de query para o subagente **leitor**, em paralelo. Ele só extrai fatos, em JSON.
- Escreva o caso literal: entrada exata, resultado esperado, resultado observado.

## 2. Reproduzir
- Reproduza com dados reais (banco local, fixture copiada do caso). Sem reprodução, não existe correção.
- Guarde o comando que reproduz. Ele vira o teste de regressão.

## 3. Hipóteses (investigador × cético)
- Liste hipóteses por camada: banco, query, service, autenticação, contrato, timing, front.
- Uma hipótese por subagente **investigador**, em paralelo. Cada um devolve evidência em `arquivo:linha`.
- Todo achado vai para o subagente **cético** antes de virar código. Se ele refutar, a hipótese cai.
- Sobrou mais de uma? Volte à reprodução e desempate com dado, não com opinião.

## 4. Corrigir
- Diff mínimo, no padrão do código ao redor. Nada de refatorar de carona.
- Teste de regressão que falha no baseline e passa no candidato.

## 5. Provar e entregar
- Rode `/validar-entrega`. Ela gera o recibo que o portão de entrega exige.
- Conclusão na tarefa com `asana_comentar`: causa, evidência, correção e como foi validado.
- Aviso para pessoas (Slack) só por `slack_rascunhar`. Quem envia é o humano que aprova.

## Regras
- Credencial nunca vai para log, comentário ou commit.
- Confira o estado real (banco, disco, API) em vez de confiar no que acha que já fez.
- Busca sempre dentro do repositório. O hook bloqueia varredura do disco.
