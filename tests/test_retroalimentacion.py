"""Unit tests for model/retroalimentacion.py: la cola de candidatas para
revisión manual, nunca auto-promovidas a faq_rrhh.json.
"""
import json

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


def test_listar_pendientes_recovers_from_a_corrupted_file(tmp_path, monkeypatch):
    """Given un archivo de retroalimentación con JSON inválido.
    When listar_pendientes() se llama.
    Then devuelve una lista vacía en vez de lanzar -- esta cola es una
    comodidad, no debe tumbar al orquestador."""
    ruta = tmp_path / "retroalimentacion.json"
    ruta.write_text("esto no es JSON válido", encoding="utf-8")
    monkeypatch.setattr(retroalimentacion, "RUTA", ruta)
    assert retroalimentacion.listar_pendientes() == []
