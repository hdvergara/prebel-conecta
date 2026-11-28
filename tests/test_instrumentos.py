"""Comprueba que los instrumentos para asistentes sigan siendo neutrales: una
sola fuente (AGENTS.md) y adaptadores sin contenido propio. No comprueba que
cada herramienta los cargue ni que un asistente los obedezca. No necesita git.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INSTRUMENTOS = RAIZ / "especificaciones" / "instrumentos"
# Archivos de instrucciones que alguna herramienta lee por su cuenta. Si
# existen, solo pueden apuntar a AGENTS.md.
OTRAS_FUENTES = ("CLAUDE.md", "GEMINI.md", "AGENTS.override.md", ".github/copilot-instructions.md",
                 ".cursorrules", ".agents/rules", ".agent/rules")


def _texto(ruta):
    return ruta.read_text(encoding="utf-8")


def test_agents_file_fits_the_codex_default_limit():
    """Given AGENTS.md, read by several tools.
    When its size is measured.
    Then it stays under Codex's default cap of 32 KiB."""
    assert (RAIZ / "AGENTS.md").stat().st_size < 32 * 1024


def test_claude_adapter_only_imports_the_shared_source():
    """Given CLAUDE.md.
    When it is read.
    Then it only imports AGENTS.md, with no instructions of its own."""
    assert _texto(RAIZ / "CLAUDE.md").split() == ["@AGENTS.md"]


def test_no_other_instruction_file_has_content_of_its_own():
    """Given the other files that tools load by themselves.
    When any exists.
    Then it is only a pointer to AGENTS.md."""
    propias = []
    for nombre in OTRAS_FUENTES:
        ruta = RAIZ / nombre
        archivos = sorted(ruta.rglob("*.md")) if ruta.is_dir() else [ruta] if ruta.is_file() else []
        propias += [a.relative_to(RAIZ).as_posix() for a in archivos if _texto(a).split() != ["@AGENTS.md"]]
    assert propias == []


def test_the_chatgpt_block_fits_the_smallest_instruction_limit():
    """Given the block to paste into ChatGPT.
    When its length is measured.
    Then it fits in 1500 characters."""
    bloque = re.search(r"```text\n(.*?)```", _texto(INSTRUMENTOS / "chatgpt.md"), re.DOTALL)[1]
    assert 0 < len(bloque) <= 1500


def test_every_instrument_is_reachable_from_the_shared_source():
    """Given the task instruments.
    When AGENTS.md is searched for them.
    Then each one is linked there."""
    agentes = _texto(RAIZ / "AGENTS.md")
    tareas = [r.name for r in INSTRUMENTOS.glob("*.md") if r.name not in {"README.md", "chatgpt.md"}]
    assert tareas and [n for n in tareas if f"especificaciones/instrumentos/{n})" not in agentes] == []
