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
import time
from datetime import datetime, timezone
from pathlib import Path

RUTA = Path(__file__).parent / "retroalimentacion.json"
_PLAZO_LOCK = 5.0  # segundos antes de darse por vencido


def registrar(pregunta: str, respuesta: str, contexto: dict) -> None:
    """read-modify-write (leer la cola completa, agregar, escribir de
    vuelta) no es atómico por sí solo, aunque _escribir_atomico() sí lo sea
    como escritura individual: dos llamadas concurrentes (dos requests de
    Flask en hilos o procesos distintos) podrían leer el mismo estado y la
    última en escribir pisaría el append de la otra ("last writer wins",
    perdiendo esa retroalimentación en silencio). _con_lock serializa el
    ciclo completo entre procesos, no solo la escritura final."""
    def _hacerlo():
        pendientes = listar_pendientes()
        pendientes.append({
            "pregunta": pregunta,
            "respuesta": respuesta,
            "contexto": contexto,
            "registrado_en": datetime.now(timezone.utc).isoformat(),
        })
        _escribir_atomico(pendientes)

    _con_lock(_hacerlo)


def _con_lock(fn):
    """Lock de archivo simple (crear un .lock exclusivo) -- funciona entre
    procesos distintos, no solo entre hilos del mismo proceso, a diferencia
    de un threading.Lock."""
    ruta_lock = RUTA.with_suffix(".lock")
    plazo = time.monotonic() + _PLAZO_LOCK
    while True:
        try:
            fd = os.open(ruta_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() >= plazo:
                raise TimeoutError("no se pudo adquirir el lock de retroalimentacion.json a tiempo")
            time.sleep(0.05)
    try:
        return fn()
    finally:
        ruta_lock.unlink(missing_ok=True)


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
    except (OSError, UnicodeError, json.JSONDecodeError):
        # Permisos, problemas del sistema de archivos, o una codificación
        # inválida son tan "no disponible" para esta cola de comodidad como
        # un JSON corrupto -- degradar a [] en los tres casos, nunca lanzar.
        return []
