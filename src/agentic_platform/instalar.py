"""Instala skills, subagentes, hooks e o servidor MCP em qualquer repositório.

    agentic-instalar /caminho/do/repo          # instala
    agentic-instalar /caminho/do/repo --dry    # só mostra o que faria

Os hooks são gravados com o caminho do Python onde este pacote está instalado, para
funcionarem mesmo dentro de um venv. Para um settings.json portátil: --python python

Não apaga nada do que já existe: hooks e servidores MCP do repositório são mantidos,
e skill/agente com o mesmo nome só é sobrescrito com --forcar.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib import resources
from pathlib import Path

MODELOS = resources.files("agentic_platform") / "claude"


def _ler_modelo(nome: str) -> dict:
    return json.loads((MODELOS / nome).read_text(encoding="utf-8"))


def _caminho_python(python: str) -> str:
    # Barra normal: no Windows o Claude Code roda hooks pelo Git Bash, que come a barra invertida.
    return python.replace("\\", "/")


def _hooks_com_python(python: str) -> dict:
    python = _caminho_python(python)
    exe = f'"{python}"' if " " in python else python
    hooks = _ler_modelo("hooks.json")
    for grupos in hooks.values():
        for g in grupos:
            for h in g["hooks"]:
                h["command"] = h["command"].replace("python -m ", f"{exe} -m ", 1)
    return hooks


def _mesclar_hooks(atuais: dict, novos: dict) -> tuple[dict, int]:
    adicionados = 0
    for evento, grupos in novos.items():
        destino = atuais.setdefault(evento, [])
        existentes = {h.get("command") for g in destino for h in g.get("hooks", [])}
        for g in grupos:
            if all(h["command"] in existentes for h in g["hooks"]):
                continue
            destino.append(g)
            adicionados += 1
    return atuais, adicionados


def instalar(repo: Path, dry: bool = False, forcar: bool = False, python: str | None = None) -> list[str]:
    repo = repo.resolve()
    if not repo.is_dir():
        raise FileNotFoundError(f"{repo} não é uma pasta")
    feito: list[str] = []
    claude = repo / ".claude"

    for tipo in ("skills", "agents"):
        for item in (MODELOS / tipo).iterdir():
            alvo = claude / tipo / item.name
            if alvo.exists() and not forcar:
                feito.append(f"mantido  .claude/{tipo}/{item.name} (já existe; use --forcar)")
                continue
            feito.append(f"copiado  .claude/{tipo}/{item.name}")
            if dry:
                continue
            alvo.parent.mkdir(parents=True, exist_ok=True)
            with resources.as_file(item) as origem:
                if origem.is_dir():
                    shutil.copytree(origem, alvo, dirs_exist_ok=True)
                else:
                    shutil.copy2(origem, alvo)

    settings_arq = claude / "settings.json"
    settings = json.loads(settings_arq.read_text(encoding="utf-8")) if settings_arq.exists() else {}
    settings["hooks"], n = _mesclar_hooks(settings.get("hooks", {}), _hooks_com_python(python or sys.executable))
    feito.append(f"hooks    .claude/settings.json (+{n} grupos)")

    mcp_arq = repo / ".mcp.json"
    mcp = json.loads(mcp_arq.read_text(encoding="utf-8")) if mcp_arq.exists() else {}
    servidores = mcp.setdefault("mcpServers", {})
    novos = {k: v for k, v in _ler_modelo("mcp_servers.json").items() if k not in servidores}
    for srv in novos.values():
        srv["command"] = _caminho_python(python or sys.executable)
    servidores.update(novos)
    feito.append(f"mcp      .mcp.json (+{len(novos)} servidor)")

    gi = repo / ".gitignore"
    linhas = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    precisa_gi = ".agentic/" not in linhas
    if precisa_gi:
        feito.append("ignore   .gitignore (+.agentic/)")

    if not dry:
        claude.mkdir(exist_ok=True)
        settings_arq.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        mcp_arq.write_text(json.dumps(mcp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if precisa_gi:
            gi.write_text("\n".join(linhas + [".agentic/"]) + "\n", encoding="utf-8")
    return feito


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", type=Path)
    ap.add_argument("--dry", action="store_true", help="não grava nada, só mostra")
    ap.add_argument("--forcar", action="store_true", help="sobrescreve skills/agentes com o mesmo nome")
    ap.add_argument("--python", help="interpretador usado nos hooks (padrão: o deste pacote)")
    a = ap.parse_args()
    for linha in instalar(a.repo, a.dry, a.forcar, a.python):
        print(linha)
    if not a.dry:
        print("\nPronto. Abra o Claude Code no repositório e rode /investigar.")


if __name__ == "__main__":
    main()
