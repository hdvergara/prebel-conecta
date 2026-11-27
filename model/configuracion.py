"""Spec-Doc editable de la cadena de capas (nivel "Data" de CONSTITUTION.md).

Los umbrales que decide model/orquestador.py viven aquí como dato, no como
constantes de código, para que cambiarlos no implique tocar orquestador.py
ni releer CONSTITUTION.md para encontrarlos: umbral_predictivo/umbral_llm
(la cadena predictivo/ML/LLM) y umbral_retroalimentacion (qué tan parecida
debe ser una pregunta a una ya resuelta por el LLM para reusar esa
respuesta sin volver a escalar -- ver model/rag_retroalimentacion.py). El
THRESHOLD de rrhh_bot.py (0.65) es distinto y no vive aquí: ese decide,
dentro de la capa ML, si confiar en el embedding.
"""
import json
from pathlib import Path

RUTA = Path(__file__).parent / "arquitectura.json"
_POR_DEFECTO = {
    "umbral_predictivo": 0.95,
    "umbral_llm": 0.75,
    "umbral_retroalimentacion": 0.85,
    "orden_capas": ["predictivo", "ml", "llm"],
}


def _validar(datos: dict) -> dict | None:
    """None si 'datos' no tiene la forma esperada (umbrales que no son
    número, fuera de [0, 1], o en el orden equivocado; orden_capas que no es
    una lista de strings) -- un JSON sintácticamente válido pero con el tipo
    equivocado (p. ej. "umbral_llm": "0.75") no debe propagarse y romper
    después una comparación entre una confianza (float) y un umbral
    (string); se trata igual que un archivo corrupto, cayendo a los
    valores por defecto. Si es válida, devuelve los umbrales ya
    convertidos a float (nunca el string crudo del JSON)."""
    try:
        umbral_predictivo = float(datos["umbral_predictivo"])
        umbral_llm = float(datos["umbral_llm"])
        umbral_retroalimentacion = float(datos["umbral_retroalimentacion"])
        orden_capas = datos["orden_capas"]
    except (TypeError, ValueError, KeyError):
        return None
    if not (0.0 <= umbral_llm <= umbral_predictivo <= 1.0):
        return None
    if not (0.0 <= umbral_retroalimentacion <= 1.0):
        return None
    if not isinstance(orden_capas, list) or not all(isinstance(c, str) for c in orden_capas):
        return None
    return {
        "umbral_predictivo": umbral_predictivo,
        "umbral_llm": umbral_llm,
        "umbral_retroalimentacion": umbral_retroalimentacion,
        "orden_capas": orden_capas,
    }


def _cargar() -> dict:
    """Si el archivo falta, está corrupto, o tiene valores con el tipo o el
    rango equivocado, se usan los valores por defecto -- este Spec-Doc es
    una comodidad editable, nunca una dependencia dura (mismo espíritu que
    R8)."""
    try:
        bruto = {**_POR_DEFECTO, **json.loads(RUTA.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError):
        return dict(_POR_DEFECTO)
    return _validar(bruto) or dict(_POR_DEFECTO)


_config = _cargar()
UMBRAL_PREDICTIVO = _config["umbral_predictivo"]
UMBRAL_LLM = _config["umbral_llm"]
UMBRAL_RETROALIMENTACION = _config["umbral_retroalimentacion"]
ORDEN_CAPAS = _config["orden_capas"]
