"""Unit tests for model/retroalimentacion.py: la cola de candidatas para
revisión manual, nunca auto-promovidas a faq_rrhh.json.
"""
import json
import threading

import retroalimentacion


# Context: retroalimentacion.RUTA apuntando a un archivo temporal por test
# (via monkeypatch), para no tocar el repositorio real.

def test_listar_pendientes_is_empty_when_no_file_exists(tmp_path, monkeypatch):
    """Given que el archivo de retroalimentación todavía no existe.
    When listar_pendientes() se llama.
    Then devuelve una lista vacía, no un error."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    assert retroalimentacion.listar_pendientes() == []


def test_registrar_appends_a_record_with_question_answer_and_context(tmp_path, monkeypatch):
    """Given una pregunta y una respuesta nuevas.
    When registrar() se llama.
    Then el registro queda en el archivo, con pregunta, respuesta, contexto
    y una marca de tiempo."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    retroalimentacion.registrar("una pregunta", "una respuesta", {"ruta": "vacaciones"})

    pendientes = retroalimentacion.listar_pendientes()
    assert len(pendientes) == 1
    assert pendientes[0]["pregunta"] == "una pregunta"
    assert pendientes[0]["respuesta"] == "una respuesta"
    assert pendientes[0]["contexto"] == {"ruta": "vacaciones"}
    assert "registrado_en" in pendientes[0]


def test_registrar_accumulates_multiple_entries(tmp_path, monkeypatch):
    """Given dos llamadas sucesivas a registrar().
    When listar_pendientes() se llama después.
    Then ambos registros están presentes, en orden."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    retroalimentacion.registrar("pregunta uno", "respuesta uno", {})
    retroalimentacion.registrar("pregunta dos", "respuesta dos", {})

    pendientes = retroalimentacion.listar_pendientes()
    assert [p["pregunta"] for p in pendientes] == ["pregunta uno", "pregunta dos"]


def test_registrar_leaves_no_stray_temp_file_behind(tmp_path, monkeypatch):
    """Given a successful registrar() call.
    When se revisa el directorio después.
    Then solo queda retroalimentacion.json -- ningún archivo temporal de la
    escritura atómica (ver _escribir_atomico) sobrevive a una escritura
    exitosa."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    retroalimentacion.registrar("una pregunta", "una respuesta", {})
    assert [p.name for p in tmp_path.iterdir()] == ["retroalimentacion.json"]


def test_listar_pendientes_recovers_from_a_corrupted_file(tmp_path, monkeypatch):
    """Given un archivo de retroalimentación con JSON inválido.
    When listar_pendientes() se llama.
    Then devuelve una lista vacía en vez de lanzar -- esta cola es una
    comodidad, no debe tumbar al orquestador."""
    ruta = tmp_path / "retroalimentacion.json"
    ruta.write_text("esto no es JSON válido", encoding="utf-8")
    monkeypatch.setattr(retroalimentacion, "RUTA", ruta)
    assert retroalimentacion.listar_pendientes() == []


class _RutaQueFallaAlLeer:
    """Un doble simple de Path que existe pero no se puede leer -- sin
    monkeypatchear Path.read_text globalmente, lo que afectaría a
    cualquier otro Path durante el test."""

    def exists(self):
        return True

    def read_text(self, **_):
        raise OSError("sin permisos")


def test_listar_pendientes_recovers_from_a_read_error(monkeypatch):
    """Given un archivo que existe pero no se puede leer (p. ej. permisos,
    o una codificación inválida para UTF-8 -- aquí simulado directamente
    con un OSError).
    When listar_pendientes() se llama.
    Then devuelve una lista vacía en vez de lanzar -- un error de lectura
    es tan "no disponible" para esta cola como uno de parseo."""
    monkeypatch.setattr(retroalimentacion, "RUTA", _RutaQueFallaAlLeer())
    assert retroalimentacion.listar_pendientes() == []


def test_concurrent_registrar_calls_do_not_lose_either_entry(tmp_path, monkeypatch):
    """Given dos hilos llamando a registrar() al mismo tiempo, cada uno con
    una pregunta distinta.
    When ambos terminan.
    Then las dos quedan registradas -- el lock de archivo serializa el
    ciclo leer-agregar-escribir completo, así que ninguno pisa al otro
    ("last writer wins" es exactamente lo que esto evita)."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")

    hilos = [
        threading.Thread(target=retroalimentacion.registrar, args=(f"pregunta {i}", f"respuesta {i}", {}))
        for i in range(2)
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    preguntas = {p["pregunta"] for p in retroalimentacion.listar_pendientes()}
    assert preguntas == {"pregunta 0", "pregunta 1"}
