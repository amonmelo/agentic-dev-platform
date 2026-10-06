# Diário de bordo

Notas do que deu errado, do que mudei de ideia e do que ainda me incomoda.
Escrevo aqui porque o README mostra o resultado, e o caminho costuma ensinar mais.

---

## Por que isso existe

Comecei a usar agente de IA no trabalho em junho. No começo era autocomplete com esteroide.
Em agosto eu já tinha skill pra puxar a demanda, subagente investigando em paralelo e cron lançando hora.

Aí veio o problema que ninguém fala: o agente mente sem querer.
Diz "corrigido" sem ter rodado o teste. Diz "validado" com mock do próprio ponto do bug.
Não é maldade, é que "pronto" é a resposta mais provável depois de editar um arquivo.

Pedir no prompt ajuda pouco. O que resolveu foi parar de pedir e começar a medir.

## Os números que me convenceram

Liguei um hook que gravava tudo. Depois de umas semanas fui olhar.

O recibo de validação tinha sido pulado em 26 de 39 rodadas que mexeram em código.
Dois terços. Eu achava que era exceção.

As buscas na raiz do disco foram piores de engolir: 46 de 52 vinham de subagente.
O agente principal sabia onde procurar. O subagente nascia sem contexto e varria o disco inteiro, às vezes por dois minutos.

Daí saíram o portão de entrega e a guarda de busca. Não foram ideia bonita. Foram resposta a um número feio.

## O cético

Esse foi o que mais mudou meu jeito de trabalhar.

Achado que parece óbvio é o mais perigoso. Tem `arquivo:linha`, faz sentido, o teste passa.
E às vezes é outro caminho do código que dá o mesmo sintoma.

Então todo achado passa por um agente cujo único trabalho é tentar derrubar.
A regra dele é: na dúvida, refuta. Parece exagero até você calcular quanto custa corrigir a coisa errada.

## Abrir isso aqui

A versão do trabalho não dá pra publicar. Chama sistema interno e tem regra de negócio dos outros.
Então reescrevi do zero, genérico, com Asana, Slack e Sheets no lugar das integrações de lá.

Achei que ia ser só limpar e subir. Não foi.

## O que quebrou quando testei de verdade (06/10/2026)

Os testes unitários estavam todos verdes. Instalei num repositório vazio e rodei o Claude Code em cima. Três coisas quebraram.

**O agente nem usou Bash.** No Windows ele foi de PowerShell. A guarda só olhava `Bash`, então o `find /` passou liso.
Óbvio depois que você vê. Eu não vi antes.

**O exit code 2 foi ignorado.** A documentação diz que exit 2 bloqueia a ferramenta. No Windows, o Claude Code registrou como "erro não bloqueante" e rodou o comando assim mesmo.
Troquei pra resposta em JSON (`permissionDecision: deny`). Funciona igual em todo lugar e ainda manda o motivo pro modelo.

**O Git Bash comeu minhas barras.** Os hooks rodam pelo Git Bash no Windows. `C:\venv\Scripts\python.exe` virava `C:venvScriptspython.exe`.
O instalador agora grava o caminho com barra normal, que o Windows aceita.

Nenhum desses aparecia em teste unitário. Por isso tem a seção "Testado com o Claude Code de verdade" no README,
e cada um virou teste novo pra não voltar.

## Coisas menores que me pegaram

O SDK do MCP mudou de versão no meio do caminho. `FastMCP` virou `MCPServer`.
E na versão nova, se a ferramenta lança `ValueError`, o modelo recebe só "Error executing tool". Sem motivo.
O agente tentava enviar um rascunho não aprovado e não sabia por que falhou. Tentava de novo. Precisa ser `ToolError` pra mensagem chegar.

E a minha máquina tinha `PYTHONOPTIMIZE=1` como variável global, sei lá desde quando.
Isso desliga `assert` em todo script Python. O pytest avisou. Eu nunca teria percebido.

## O que ainda me incomoda

- O portão confia no recibo. Um agente esperto pode gerar recibo com evidência inventada.
  O próximo passo é cruzar com o log: o comando do teste rodou mesmo, e passou?
- As métricas são por repositório. Eu queria ver vários projetos juntos num painel.
- A aprovação humana é por linha de comando. Num time de verdade isso seria um botão no próprio Slack.

Se você chegou até aqui e tem ideia pra algum desses, abre uma issue. Vou gostar de ler.
