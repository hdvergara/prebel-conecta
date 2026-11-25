"""Cola de retroalimentación hacia las capas anteriores (el "retorno en
forma inversa" ratificado): cuando el conector LLM responde algo que la capa
ML no tenía con confianza, esa pregunta/respuesta se guarda aquí como
candidata -- nunca se escribe sola en faq_rrhh.json. Promoverla al FAQ real
sigue siendo una decisión manual de quien la revise (ver
model/entrenar.py --revisar-retroalimentacion), en el mismo espíritu que
CONSTITUTION.md R1/R4: nada entra al FAQ curado sin que alguien lo decida a
propósito.

model/retroalimentacion.json es estado generado en ejecución, no una fuente
de datos curada -- está en .gitignore, igual que model/faq_embeddings.pt.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

RUTA = Path(__file__).parent / "retroalimentacion.json"


def registrar(pregunta: str, respuesta: str, contexto: dict) -> None:
    pendientes = listar_pendientes()
    pendientes.append({
        "pregunta": pregunta,
        "respuesta": respuesta,
        "contexto": contexto,
        "registrado_en": datetime.now(timezone.utc).isoformat(),
    })
    RUTA.write_text(json.dumps(pendientes, ensure_ascii=False, indent=2), encoding="utf-8")


def listar_pendientes() -> list:
    if not RUTA.exists():
        return []
    try:
        return json.loads(RUTA.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
