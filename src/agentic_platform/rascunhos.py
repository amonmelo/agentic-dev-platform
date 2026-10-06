"""Fila de mensagens com aprovação humana.

Regra da plataforma: o agente pode escrever para fora (Slack, e-mail, comentário em
tarefa), mas nada sai sem um humano aprovar. O agente cria o rascunho; a pessoa aprova
com `agentic-aprovar <id>`; só então a ferramenta de envio aceita.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from agentic_platform import estado

SCHEMA = """
create table if not exists rascunho (
    id text primary key,
    canal text not null,
    destino text not null,
    texto text not null,
    status text not null default 'pendente',  -- pendente | aprovado | enviado | rejeitado
    criado_em text not null,
    atualizado_em text not null
)
"""


def _conn(cwd: str | None = None) -> sqlite3.Connection:
    c = sqlite3.connect(Path(estado.pasta(cwd)) / "rascunhos.db")
    c.row_factory = sqlite3.Row
    c.execute(SCHEMA)
    return c


def criar(canal: str, destino: str, texto: str, cwd: str | None = None) -> dict:
    rid = uuid.uuid4().hex[:8]
    t = estado.agora()
    with _conn(cwd) as c:
        c.execute("insert into rascunho values (?,?,?,?,'pendente',?,?)", (rid, canal, destino, texto, t, t))
    return obter(rid, cwd)


def obter(rid: str, cwd: str | None = None) -> dict | None:
    with _conn(cwd) as c:
        r = c.execute("select * from rascunho where id=?", (rid,)).fetchone()
    return dict(r) if r else None


def listar(status: str | None = None, cwd: str | None = None) -> list[dict]:
    with _conn(cwd) as c:
        q = "select * from rascunho" + (" where status=?" if status else "") + " order by criado_em"
        return [dict(r) for r in c.execute(q, (status,) if status else ())]


def mudar_status(rid: str, novo: str, cwd: str | None = None) -> dict:
    atual = obter(rid, cwd)
    if not atual:
        raise KeyError(f"rascunho {rid} não existe")
    permitido = {"pendente": {"aprovado", "rejeitado"}, "aprovado": {"enviado", "rejeitado"}}
    if novo not in permitido.get(atual["status"], set()):
        raise ValueError(f"rascunho {rid} está '{atual['status']}', não pode virar '{novo}'")
    with _conn(cwd) as c:
        c.execute("update rascunho set status=?, atualizado_em=? where id=?", (novo, estado.agora(), rid))
    return obter(rid, cwd)
