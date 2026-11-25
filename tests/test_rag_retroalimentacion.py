"""Unit tests for model/rag_retroalimentacion.py: el reuso por similitud
sobre la cola de retroalimentación, antes de escalar de verdad al conector
LLM. Usa FakeSentenceTransformer (tests/fakes.py) -- mismo texto da
similitud 1.0, textos distintos dan similitud cercana a 0 -- así que la
"coincidencia fuerte" en estos tests es, a propósito, el mismo texto ya
registrado antes.
"""
import retroalimentacion
from fakes import FakeSentenceTransformer
from rag_retroalimentacion import buscar_similar


# Context: retroalimentacion.RUTA apuntando a un archivo temporal por test
# (via monkeypatch), con un FakeSentenceTransformer como "modelo" inyectado.

def test_an_empty_queue_returns_none(tmp_path, monkeypatch):
    """Given ninguna entrada registrada todavía.
    When buscar_similar() se llama.
    Then devuelve None -- no hay nada que reusar."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    assert buscar_similar(FakeSentenceTransformer(), "una pregunta cualquiera") is None


def test_an_exact_match_in_the_queue_is_reused(tmp_path, monkeypatch):
    """Given una entrada ya registrada con exactamente el mismo texto.
    When buscar_similar() se llama con ese mismo texto.
    Then devuelve esa respuesta -- similitud 1.0 con FakeSentenceTransformer,
    muy por encima de UMBRAL_RETROALIMENTACION."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    retroalimentacion.registrar("cuanto dura la licencia de paternidad", "14 dias calendario.", {"ruta": "licencias"})

    resultado = buscar_similar(FakeSentenceTransformer(), "cuanto dura la licencia de paternidad")
    assert resultado == {"respuesta": "14 dias calendario.", "contexto": {"ruta": "licencias"}}


def test_an_unrelated_question_returns_none(tmp_path, monkeypatch):
    """Given una entrada registrada para un tema distinto.
    When buscar_similar() se llama con un texto sin relación.
    Then devuelve None -- FakeSentenceTransformer da similitud cercana a 0
    entre textos distintos, por debajo de UMBRAL_RETROALIMENTACION."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    retroalimentacion.registrar("cuanto dura la licencia de paternidad", "14 dias calendario.", {})

    assert buscar_similar(FakeSentenceTransformer(), "como solicito un certificado laboral") is None


def test_picks_the_best_match_among_several_entries(tmp_path, monkeypatch):
    """Given varias entradas registradas, ninguna idéntica a la consulta.
    When buscar_similar() se llama con el texto exacto de una de ellas.
    Then reusa esa, no otra -- se queda con el mejor puntaje, no el primero
    ni uno cualquiera."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    retroalimentacion.registrar("pregunta uno", "respuesta uno", {})
    retroalimentacion.registrar("pregunta dos", "respuesta dos", {})
    retroalimentacion.registrar("pregunta tres", "respuesta tres", {})

    resultado = buscar_similar(FakeSentenceTransformer(), "pregunta dos")
    assert resultado["respuesta"] == "respuesta dos"


def test_never_raises_if_an_entry_is_malformed(tmp_path, monkeypatch):
    """Given una entrada en la cola sin la clave "pregunta" (corrupta o de
    un formato viejo).
    When buscar_similar() se llama.
    Then devuelve None en vez de lanzar -- esta búsqueda es una optimización,
    nunca debe tumbar la cadena si la cola tiene algo inesperado."""
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    (tmp_path / "retroalimentacion.json").write_text('[{"respuesta": "sin pregunta"}]', encoding="utf-8")

    assert buscar_similar(FakeSentenceTransformer(), "cualquier cosa") is None
