import json
from pathlib import Path

from agentic_platform.instalar import instalar

RAIZ = Path(__file__).resolve().parents[1]


def test_instala_num_repo_vazio(tmp_path):
    instalar(tmp_path)
    assert (tmp_path / ".claude/skills/investigar/SKILL.md").exists()
    assert (tmp_path / ".claude/agents/cetico.md").exists()
    hooks = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))["hooks"]
    assert {"PreToolUse", "PostToolUse", "Stop", "SessionStart"} <= hooks.keys()
    assert "agentic" in json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    assert ".agentic/" in (tmp_path / ".gitignore").read_text(encoding="utf-8")


def test_preserva_o_que_o_repo_ja_tinha(tmp_path):
    (tmp_path / ".claude/skills/investigar").mkdir(parents=True)
    (tmp_path / ".claude/skills/investigar/SKILL.md").write_text("minha versão", encoding="utf-8")
    (tmp_path / ".claude/settings.json").write_text(json.dumps({
        "permissions": {"allow": ["Bash(npm test)"]},
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "./meu-hook.sh"}]}]},
    }), encoding="utf-8")
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"github": {"command": "gh-mcp"}}}), encoding="utf-8")

    instalar(tmp_path)

    assert (tmp_path / ".claude/skills/investigar/SKILL.md").read_text(encoding="utf-8") == "minha versão"
    s = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert s["permissions"] == {"allow": ["Bash(npm test)"]}
    comandos = [h["command"] for g in s["hooks"]["Stop"] for h in g["hooks"]]
    assert "./meu-hook.sh" in comandos and any("portao_entrega" in c for c in comandos)
    assert set(json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]) == {"github", "agentic"}


def test_rodar_duas_vezes_nao_duplica(tmp_path):
    instalar(tmp_path)
    antes = (tmp_path / ".claude/settings.json").read_text(encoding="utf-8")
    saida = instalar(tmp_path)
    assert (tmp_path / ".claude/settings.json").read_text(encoding="utf-8") == antes
    assert any("+0 grupos" in linha for linha in saida)


def test_dry_nao_grava_nada(tmp_path):
    instalar(tmp_path, dry=True)
    assert list(tmp_path.iterdir()) == []


def test_este_repositorio_usa_a_propria_plataforma():
    """O .claude/ versionado aqui é o mesmo que o instalador entrega. Se divergir, o teste avisa."""
    pacote = RAIZ / "src/agentic_platform/claude"
    for arq in [*pacote.glob("agents/*.md"), *pacote.glob("skills/*/SKILL.md")]:
        rel = arq.relative_to(pacote)
        assert (RAIZ / ".claude" / rel).read_text(encoding="utf-8") == arq.read_text(encoding="utf-8"), rel


def test_hooks_usam_o_python_escolhido(tmp_path):
    instalar(tmp_path, python="/opt/venv/bin/python")
    s = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for grupos in s["hooks"].values() for g in grupos for h in g["hooks"]]
    assert comandos and all(c.startswith("/opt/venv/bin/python -m agentic_platform.hooks.") for c in comandos)


def test_hooks_aspas_quando_o_caminho_tem_espaco(tmp_path):
    instalar(tmp_path, python="C:/Program Files/Python311/python.exe")
    s = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert s["hooks"]["Stop"][0]["hooks"][0]["command"].startswith('"C:/Program Files/Python311/python.exe" -m ')


def test_caminho_windows_vira_barra_normal(tmp_path):
    """No Windows o Claude Code roda hooks pelo Git Bash, que come a barra invertida."""
    instalar(tmp_path, python=r"C:\venv\Scripts\python.exe")
    s = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert s["hooks"]["Stop"][0]["hooks"][0]["command"].startswith("C:/venv/Scripts/python.exe -m ")
    mcp = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["agentic"]["command"] == "C:/venv/Scripts/python.exe"
    assert mcp["mcpServers"]["agentic"]["args"] == ["-m", "agentic_platform.mcp_server"]
