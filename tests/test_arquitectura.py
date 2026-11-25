"""Hace cumplible, no solo documentada, la separación de capas de
CONSTITUTION.md R9: la capa ML (rrhh_bot.py) nunca debe conocer al conector
LLM ni al orquestador -- solo model/orquestador.py puede hablarle a
model/conectores.py. Se revisa por AST (sin ejecutar el archivo) para que
esto no dependa de tener los modelos pesados disponibles.
"""
import ast
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[1] / "model"


def _modulos_importados(ruta: Path) -> set:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module)
    return modulos


# Context: los archivos fuente de model/, leídos directamente del disco.

def test_rrhh_bot_never_imports_the_llm_connector_or_the_orchestrator():
    """Given model/rrhh_bot.py (la capa ML/semántica).
    When se listan sus imports.
    Then no incluyen conectores ni orquestador -- esa capa no sabe que el
    LLM existe; escalar a él es decisión exclusiva del orquestador."""
    modulos = _modulos_importados(MODEL_DIR / "rrhh_bot.py")
    assert "conectores" not in modulos
    assert "orquestador" not in modulos


def test_conectores_never_imports_rrhh_bot():
    """Given model/conectores.py (la capa LLM/agéntica).
    When se listan sus imports.
    Then no incluye rrhh_bot -- el conector no conoce la lógica semántica;
    solo recibe el contexto (ruta/area) que el orquestador ya le pasa."""
    modulos = _modulos_importados(MODEL_DIR / "conectores.py")
    assert "rrhh_bot" not in modulos


def test_only_the_orchestrator_imports_the_connector_module():
    """Given todos los archivos .py de model/.
    When se busca quién importa conectores.py.
    Then solo orquestador.py lo hace -- ningún otro módulo alcanza al LLM
    por su cuenta."""
    importadores = {
        ruta.stem for ruta in MODEL_DIR.glob("*.py")
        if ruta.stem != "conectores" and "conectores" in _modulos_importados(ruta)
    }
    assert importadores == {"orquestador"}
