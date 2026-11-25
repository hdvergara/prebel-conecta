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
import os
import tempfile
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
    _escribir_atomico(pendientes)


def _escribir_atomico(pendientes: list) -> None:
    """Escribe en un archivo temporal y lo renombra encima de RUTA
    (os.replace es atómico en el mismo disco), no RUTA.write_text()
    directo -- si el proceso se interrumpe a mitad de una escritura
    directa, o dos requests escriben a la vez, el JSON puede quedar
    truncado/corrupto, y listar_pendientes() lo descartaría en silencio
    (devuelve [] ante JSON inválido), perdiendo la retroalimentación ya
    registrada."""
    fd, nombre_temporal = tempfile.mkstemp(dir=RUTA.parent, prefix=".retroalimentacion-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as archivo_temporal:
            json.dump(pendientes, archivo_temporal, ensure_ascii=False, indent=2)
        os.replace(nombre_temporal, RUTA)
    except Exception:
        Path(nombre_temporal).unlink(missing_ok=True)
        raise


def listar_pendientes() -> list:
    if not RUTA.exists():
        return []
    try:
        return json.loads(RUTA.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
