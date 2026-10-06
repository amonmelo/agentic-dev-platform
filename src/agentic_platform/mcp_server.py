"""Servidor MCP que dá aos agentes acesso a Asana, Slack e Google Sheets.

Leitura é livre. Escrita interna (tarefa, comentário) é direta. Mensagem para pessoas
(Slack) passa pela fila de aprovação: o agente cria o rascunho e só envia o que um
humano aprovou com `agentic-aprovar`.

Registro no Claude Code: veja `.mcp.json` na raiz do repositório.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from agentic_platform import rascunhos
from agentic_platform.integracoes import montar

asana, slack, sheets = montar()

mcp = MCPServer(
    name="agentic-dev-platform",
    instructions=(
        "Ferramentas de trabalho do time. Para falar com pessoas no Slack, use slack_rascunhar "
        "e espere o humano aprovar; slack_enviar só aceita rascunho aprovado."
    ),
)


@mcp.tool()
def asana_listar_tarefas(projeto: str) -> list[dict]:
    """Lista as tarefas de um projeto do Asana (nome, status, prazo)."""
    return asana.listar_tarefas(projeto)


@mcp.tool()
def asana_criar_tarefa(projeto: str, nome: str, notas: str = "") -> dict:
    """Cria uma tarefa no projeto do Asana."""
    return asana.criar_tarefa(projeto, nome, notas)


@mcp.tool()
def asana_comentar(tarefa: str, texto: str) -> dict:
    """Comenta numa tarefa do Asana (ex.: conclusão da investigação com as evidências)."""
    return asana.comentar(tarefa, texto)


@mcp.tool()
def sheets_ler(planilha: str, intervalo: str = "A1:Z200") -> list[list[str]]:
    """Lê um intervalo de uma planilha do Google Sheets."""
    return sheets.ler(planilha, intervalo)


@mcp.tool()
def slack_rascunhar(canal: str, texto: str) -> dict:
    """Cria um rascunho de mensagem para o Slack. NÃO envia: um humano precisa aprovar."""
    r = rascunhos.criar("slack", canal, texto)
    return {"id": r["id"], "status": r["status"], "proximo_passo": f"peça para aprovarem: agentic-aprovar {r['id']}"}


@mcp.tool()
def slack_enviar(rascunho_id: str) -> dict:
    """Envia um rascunho JÁ APROVADO por um humano. Recusa rascunho pendente ou rejeitado."""
    r = rascunhos.obter(rascunho_id)
    if not r:
        raise ToolError(f"rascunho {rascunho_id} não existe")
    if r["status"] != "aprovado":
        raise ToolError(f"rascunho {rascunho_id} está '{r['status']}'; só envio o que foi aprovado")
    enviado = slack.postar(r["destino"], r["texto"])
    rascunhos.mudar_status(rascunho_id, "enviado")
    return {"enviado": True, **enviado}


@mcp.tool()
def rascunhos_pendentes() -> list[dict]:
    """Lista os rascunhos que ainda esperam aprovação humana."""
    return rascunhos.listar("pendente")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
