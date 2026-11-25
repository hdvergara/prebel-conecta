"""Spec-Doc editable de la cadena de capas (ver CONSTITUTION.md R9).

Los dos umbrales que decide model/orquestador.py viven aquí como dato, no
como constantes de código, para que cambiarlos no implique tocar
orquestador.py ni releer CONSTITUTION.md para encontrarlos. El THRESHOLD de
rrhh_bot.py (0.65) es distinto y no vive aquí: ese decide, dentro de la capa
ML, si confiar en el embedding; estos dos son del orquestador, una capa
arriba de ese.
"""
import json
from pathlib import Path

RUTA = Path(__file__).parent / "arquitectura.json"
_POR_DEFECTO = {"umbral_predictivo": 0.95, "umbral_llm": 0.75, "orden_capas": ["predictivo", "ml", "llm"]}


def _cargar() -> dict:
    """Si el archivo falta o está corrupto, se usan los valores por
    defecto -- este Spec-Doc es una comodidad editable, nunca una
    dependencia dura (mismo espíritu que R2/R8)."""
    try:
        return {**_POR_DEFECTO, **json.loads(RUTA.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError):
        return dict(_POR_DEFECTO)


_config = _cargar()
UMBRAL_PREDICTIVO = _config["umbral_predictivo"]
UMBRAL_LLM = _config["umbral_llm"]
ORDEN_CAPAS = _config["orden_capas"]
