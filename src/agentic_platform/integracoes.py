"""Clientes das integrações (Asana, Slack, Google Sheets) com um modo demo offline.

Sem token configurado, cada integração cai no modo demo: dados em memória e envios
registrados localmente. Assim o servidor MCP roda e é testável sem conta em nada.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field


class ErroIntegracao(RuntimeError):
    pass


def _http(metodo: str, url: str, token: str, corpo: dict | None = None) -> dict:
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise ErroIntegracao(f"{metodo} {url} -> HTTP {e.code}: {e.read()[:300]!r}") from e


# --- Asana -------------------------------------------------------------------

class Asana:
    BASE = "https://app.asana.com/api/1.0"

    def __init__(self, token: str):
        self.token = token

    def listar_tarefas(self, projeto: str) -> list[dict]:
        q = urllib.parse.urlencode({"project": projeto, "opt_fields": "name,completed,assignee.name,due_on"})
        return _http("GET", f"{self.BASE}/tasks?{q}", self.token)["data"]

    def criar_tarefa(self, projeto: str, nome: str, notas: str = "") -> dict:
        return _http("POST", f"{self.BASE}/tasks", self.token,
                     {"data": {"name": nome, "notes": notas, "projects": [projeto]}})["data"]

    def comentar(self, tarefa: str, texto: str) -> dict:
        return _http("POST", f"{self.BASE}/tasks/{tarefa}/stories", self.token, {"data": {"text": texto}})["data"]


# --- Slack -------------------------------------------------------------------

class Slack:
    def __init__(self, token: str):
        self.token = token

    def postar(self, canal: str, texto: str) -> dict:
        r = _http("POST", "https://slack.com/api/chat.postMessage", self.token, {"channel": canal, "text": texto})
        if not r.get("ok"):
            raise ErroIntegracao(f"Slack recusou: {r.get('error')}")
        return {"canal": r["channel"], "ts": r["ts"]}


# --- Google Sheets -----------------------------------------------------------

class Sheets:
    def __init__(self, token: str):
        self.token = token

    def ler(self, planilha: str, intervalo: str) -> list[list[str]]:
        url = (f"https://sheets.googleapis.com/v4/spreadsheets/{planilha}/values/"
               f"{urllib.parse.quote(intervalo)}")
        return _http("GET", url, self.token).get("values", [])


# --- Modo demo ---------------------------------------------------------------

def _tarefas_demo() -> dict[str, list[dict]]:
    return {
        "demo": [
            {"gid": "1", "name": "Erro 500 ao exportar relatório de NPS", "completed": False, "due_on": "2026-10-09"},
            {"gid": "2", "name": "Sincronizar clientes CRM x ERP", "completed": False, "due_on": "2026-10-12"},
            {"gid": "3", "name": "Revisar permissões por papel", "completed": True, "due_on": None},
        ]
    }


def _planilhas_demo() -> dict[str, list[list[str]]]:
    return {"demo": [["cliente", "nps"], ["Fazenda Boa Vista", "9"], ["Agro Cerrado", "6"]]}


@dataclass
class Demo:
    """Implementa a mesma interface das três integrações, em memória."""

    tarefas: dict[str, list[dict]] = field(default_factory=_tarefas_demo)
    comentarios: list[dict] = field(default_factory=list)
    enviados: list[dict] = field(default_factory=list)
    planilhas: dict[str, list[list[str]]] = field(default_factory=_planilhas_demo)

    def listar_tarefas(self, projeto: str) -> list[dict]:
        return self.tarefas.get(projeto, [])

    def criar_tarefa(self, projeto: str, nome: str, notas: str = "") -> dict:
        total = sum(len(v) for v in self.tarefas.values())
        t = {"gid": str(total + 1), "name": nome, "notes": notas, "completed": False, "due_on": None}
        self.tarefas.setdefault(projeto, []).append(t)
        return t

    def comentar(self, tarefa: str, texto: str) -> dict:
        c = {"tarefa": tarefa, "text": texto}
        self.comentarios.append(c)
        return c

    def postar(self, canal: str, texto: str) -> dict:
        self.enviados.append({"canal": canal, "texto": texto})
        return {"canal": canal, "ts": f"demo-{len(self.enviados)}"}

    def ler(self, planilha: str, intervalo: str) -> list[list[str]]:
        return self.planilhas.get(planilha, [])


def montar():
    """Retorna (asana, slack, sheets): cliente real se houver token no ambiente, demo se não."""
    demo = Demo()
    asana = Asana(os.environ["ASANA_TOKEN"]) if os.environ.get("ASANA_TOKEN") else demo
    slack = Slack(os.environ["SLACK_BOT_TOKEN"]) if os.environ.get("SLACK_BOT_TOKEN") else demo
    sheets = Sheets(os.environ["GOOGLE_ACCESS_TOKEN"]) if os.environ.get("GOOGLE_ACCESS_TOKEN") else demo
    return asana, slack, sheets
