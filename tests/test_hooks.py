import json

import pytest

from agentic_platform import estado, recibo


def bash(cmd, sessao="s1", evento="PreToolUse", **extra):
    return {"session_id": sessao, "hook_event_name": evento, "tool_name": "Bash",
            "tool_input": {"command": cmd}, **extra}


def edicao(sessao="s1"):
    return {"session_id": sessao, "hook_event_name": "PostToolUse", "tool_name": "Edit",
            "tool_input": {"file_path": "src/app.py"}, "tool_response": {"success": True}}


# --- guarda de busca --------------------------------------------------------

def negado(r) -> bool:
    if r.returncode != 0 or not r.stdout.strip():
        return False
    saida = json.loads(r.stdout)["hookSpecificOutput"]
    return saida["permissionDecision"] == "deny" and "Bloqueado" in saida["permissionDecisionReason"]


@pytest.mark.parametrize("cmd", [
    "find / -name '*.py'",
    "grep -rn senha /",
    "find C:\\ -iname config.json",
    "du -sh ~",
])
def test_guarda_bloqueia_busca_na_raiz(rodar_hook, cmd):
    assert negado(rodar_hook("guarda_busca", bash(cmd)))


@pytest.mark.parametrize("cmd", [
    "find src -name '*.py'",
    "grep -rn TODO src/ tests/",
    "ls /",
    "python -m pytest -q",
])
def test_guarda_deixa_passar_busca_no_repo(rodar_hook, cmd):
    r = rodar_hook("guarda_busca", bash(cmd))
    assert r.returncode == 0 and r.stdout.strip() == ""


@pytest.mark.parametrize("cmd", [
    r"Get-ChildItem -Path C:\ -Recurse -Filter *.env",
    r"gci C:\ -r -Include settings.py",
    "dir /s C:\\",
    "find / -maxdepth 1 -name nada",
])
def test_guarda_bloqueia_busca_na_raiz_no_powershell(rodar_hook, cmd):
    assert negado(rodar_hook("guarda_busca", {"tool_name": "PowerShell", "tool_input": {"command": cmd}}))


@pytest.mark.parametrize("cmd", ["Get-ChildItem -Path src -Recurse", "Get-ChildItem C:\\", "dir"])
def test_guarda_deixa_passar_powershell_no_repo(rodar_hook, cmd):
    r = rodar_hook("guarda_busca", {"tool_name": "PowerShell", "tool_input": {"command": cmd}})
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_guarda_bloqueia_grep_tool_na_raiz(rodar_hook):
    assert negado(rodar_hook("guarda_busca", {"tool_name": "Grep", "tool_input": {"pattern": "x", "path": "C:\\"}}))


# --- observabilidade --------------------------------------------------------

def test_observabilidade_grava_evento_com_agente(rodar_hook):
    r = rodar_hook("observabilidade", bash("pytest -q", evento="PostToolUse", agent_type="investigador"))
    assert r.returncode == 0
    (ev,) = estado.eventos()
    assert ev["ferramenta"] == "Bash"
    assert ev["agente"] == "investigador"
    assert ev["alvo"] == "pytest -q"
    assert ev["falhou"] is False


def test_observabilidade_marca_falha(rodar_hook):
    rodar_hook("observabilidade", bash("pytest -q", evento="PostToolUseFailure"))
    assert estado.eventos()[0]["falhou"] is True


# --- portão de entrega ------------------------------------------------------

def stop(sessao="s1", ativo=False):
    return {"session_id": sessao, "hook_event_name": "Stop", "stop_hook_active": ativo}


def test_portao_libera_sessao_sem_edicao(rodar_hook):
    assert rodar_hook("portao_entrega", stop()).stdout.strip() == ""


def test_portao_bloqueia_edicao_sem_recibo(rodar_hook):
    rodar_hook("observabilidade", edicao())
    saida = json.loads(rodar_hook("portao_entrega", stop()).stdout)
    assert saida["decision"] == "block"
    assert "validar-entrega" in saida["reason"]


def test_portao_libera_com_recibo_depois_da_edicao(rodar_hook):
    rodar_hook("observabilidade", edicao())
    recibo.gerar(True, ["pytest: 14 passed"])
    assert rodar_hook("portao_entrega", stop()).stdout.strip() == ""


def test_portao_nao_aceita_recibo_reprovado(rodar_hook):
    rodar_hook("observabilidade", edicao())
    recibo.gerar(False, ["E2E falhou no passo 3"])
    assert json.loads(rodar_hook("portao_entrega", stop()).stdout)["decision"] == "block"


def test_portao_nao_entra_em_loop(rodar_hook):
    rodar_hook("observabilidade", edicao())
    assert rodar_hook("portao_entrega", stop(ativo=True)).stdout.strip() == ""


def test_portao_ignora_edicao_de_outra_sessao(rodar_hook):
    rodar_hook("observabilidade", edicao(sessao="outra"))
    assert rodar_hook("portao_entrega", stop(sessao="s1")).stdout.strip() == ""


def test_recibo_aprovado_exige_evidencia():
    with pytest.raises(ValueError):
        recibo.gerar(True, [])


# --- retomada após compactação ----------------------------------------------

def test_retomada_devolve_estado_depois_de_compactar(rodar_hook, pasta_agentic):
    estado.gravar_json(estado.pasta() / "estado.json", {
        "tarefa": "NPS-42", "etapa": "3-hipoteses", "proximo_passo": "rodar o cético no achado do service",
        "definicao_de_pronto": "teste de regressão passa no candidato",
    })
    saida = json.loads(rodar_hook("retomada", {"source": "compact"}).stdout)
    ctx = saida["hookSpecificOutput"]["additionalContext"]
    assert "NPS-42" in ctx and "3-hipoteses" in ctx and "cético" in ctx


def test_retomada_fica_quieta_em_sessao_nova(rodar_hook):
    estado.gravar_json(estado.pasta() / "estado.json", {"tarefa": "x"})
    assert rodar_hook("retomada", {"source": "startup"}).stdout.strip() == ""
