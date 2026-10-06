"""O servidor MCP testado de ponta a ponta: processo real, protocolo real, via stdio."""
import asyncio
import json
import os
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agentic_platform import rascunhos


async def _sessao(acoes):
    params = StdioServerParameters(command=sys.executable, args=["-m", "agentic_platform.mcp_server"],
                                   env={**os.environ})
    async with stdio_client(params) as (leitura, escrita, *_):
        async with ClientSession(leitura, escrita) as s:
            await s.initialize()
            return await acoes(s)


def rodar(acoes):
    return asyncio.run(asyncio.wait_for(_sessao(acoes), timeout=60))


def texto(res):
    return json.loads(res.content[0].text)


def test_expoe_as_ferramentas_esperadas():
    async def acoes(s):
        return {t.name for t in (await s.list_tools()).tools}

    assert rodar(acoes) >= {"asana_listar_tarefas", "asana_criar_tarefa", "asana_comentar",
                             "sheets_ler", "slack_rascunhar", "slack_enviar", "rascunhos_pendentes"}


def test_le_asana_e_sheets_no_modo_demo():
    async def acoes(s):
        t = await s.call_tool("asana_listar_tarefas", {"projeto": "demo"})
        p = await s.call_tool("sheets_ler", {"planilha": "demo"})
        return t, p

    tarefas, planilha = rodar(acoes)
    assert "Erro 500 ao exportar" in tarefas.content[0].text
    assert "Agro Cerrado" in planilha.content[0].text or "Agro Cerrado" in json.dumps(planilha.structured_content)


def test_slack_so_envia_depois_de_aprovacao_humana():
    async def rascunhar(s):
        return texto(await s.call_tool("slack_rascunhar", {"canal": "#sustentacao", "texto": "Corrigido o NPS."}))

    r = rodar(rascunhar)
    assert r["status"] == "pendente"

    async def enviar(s):
        return await s.call_tool("slack_enviar", {"rascunho_id": r["id"]})

    recusado = rodar(enviar)
    assert recusado.is_error and "pendente" in recusado.content[0].text

    rascunhos.mudar_status(r["id"], "aprovado")  # o humano aprova (agentic-aprovar)
    enviado = rodar(enviar)
    assert not enviado.is_error
    assert rascunhos.obter(r["id"])["status"] == "enviado"

    de_novo = rodar(enviar)
    assert de_novo.is_error  # não reenvia


def test_rascunho_rejeitado_nao_volta():
    r = rascunhos.criar("slack", "#geral", "texto")
    rascunhos.mudar_status(r["id"], "rejeitado")
    with pytest.raises(ValueError):
        rascunhos.mudar_status(r["id"], "aprovado")
