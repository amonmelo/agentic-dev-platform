from agentic_platform.metricas import calcular, diagnosticar


def ev(sessao, ferramenta, alvo="", evento="PostToolUse", agente="principal", falhou=False):
    return {"sessao": sessao, "evento": evento, "ferramenta": ferramenta,
            "alvo": alvo, "agente": agente, "falhou": falhou}


def test_conta_sessoes_que_editaram_sem_recibo():
    eventos = [
        ev("a", "Edit", "src/x.py"), ev("a", "Bash", "agentic-recibo --aprovado --evidencia ok"),
        ev("b", "Edit", "src/y.py"),
        ev("c", "Write", "src/z.py"),
        ev("d", "Read", "README.md"),
    ]
    m = calcular(eventos)
    assert m["sessoes"] == 4
    assert m["sessoes_que_editaram"] == 3
    assert m["editaram_sem_recibo"] == 2


def test_separa_busca_na_raiz_por_agente():
    eventos = [
        ev("a", "Bash", "find / -name x", evento="PreToolUse", agente="investigador"),
        ev("a", "Bash", "find / -name y", evento="PreToolUse", agente="investigador"),
        ev("a", "Bash", "grep -rn z /", evento="PreToolUse"),
        ev("a", "Bash", "find src -name x", evento="PreToolUse", agente="investigador"),
    ]
    assert calcular(eventos)["buscas_na_raiz_por_agente"] == {"investigador": 2, "principal": 1}


def test_diagnostico_aponta_o_que_mexer():
    eventos = (
        [ev(f"s{i}", "Edit", "src/a.py") for i in range(5)]
        + [ev("s0", "Bash", "agentic-recibo --aprovado --evidencia ok")]
        + [ev("s1", "Bash", "find / -name x", evento="PreToolUse", agente="leitor")]
        + [ev("s2", "Bash", "pytest", evento="PostToolUseFailure", falhou=True) for _ in range(3)]
    )
    rec = " ".join(diagnosticar(calcular(eventos)))
    assert "80% das sessões" in rec
    assert "1 vindas de subagentes" in rec
    assert "Bash falhou 3" in rec
    assert "cético" in rec  # nenhum subagente revisou


def test_diagnostico_silencioso_quando_tudo_bem():
    eventos = [ev("a", "Edit", "x.py"), ev("a", "Bash", "agentic-recibo --aprovado --evidencia ok"),
               ev("a", "Task", evento="SubagentStop", agente="cetico")]
    assert diagnosticar(calcular(eventos)) == ["Nada fora do esperado nos limites atuais."]


def test_exemplo_do_readme_bate_com_a_saida_real():
    """A saída mostrada no README vem de examples/log_demo.py. Se o código mudar, isto avisa."""
    import importlib.util
    from pathlib import Path

    arq = Path(__file__).resolve().parents[1] / "examples/log_demo.py"
    spec = importlib.util.spec_from_file_location("log_demo", arq)
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    m = calcular(demo.gerar())
    assert (m["sessoes_que_editaram"], m["editaram_sem_recibo"]) == (39, 26)
    assert m["buscas_na_raiz_por_agente"] == {"investigador": 46, "principal": 6}
    assert diagnosticar(m)[0].startswith("66% das sessões")
