"""Unit tests for the Flask API's JSON contract (/reply).

Per CONSTITUTION.md "Harness": the real models are faked here too; this suite
only verifies the HTTP/JSON shape rrhh_api.py exposes. RRHHBot's own matching
logic is covered by test_rrhh_bot.py, so it isn't re-verified here.
"""
import sys
from unittest.mock import patch

import pytest

from fakes import FakeSentenceTransformer, FakeSentimentPipeline


@pytest.fixture
def client():
    """Fresh Flask test client per test. rrhh_api is force-reimported inside
    the patch context so its module-level `bot = RRHHBot()` runs against the
    fakes, not the real ~1GB models."""
    import rrhh_bot

    sys.modules.pop("rrhh_api", None)
    with patch.object(rrhh_bot, "SentenceTransformer", return_value=FakeSentenceTransformer()), \
         patch.object(rrhh_bot, "pipeline", return_value=FakeSentimentPipeline({"hola": ("5 stars", 0.8)})):
        import rrhh_api

    yield rrhh_api.app.test_client()
    sys.modules.pop("rrhh_api", None)


# Context: a fresh Flask test client per test, backed by the real
# model/faq_rrhh.json content (harmless -- only the ML models are faked).

def test_reply_with_text_returns_full_json_contract(client):
    """Given a POST with non-empty text.
    When /reply handles it.
    Then the response is 200 JSON with exactly the documented keys,
    including 'guia', 'tipo' and 'capa' (ver FLUJOS.md -- el orquestador siempre informa cuál
    capa respondió, sin que el llamador tenga que adivinarlo)."""
    resp = client.post("/reply", json={"text": "hola"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {"reply", "ruta", "area", "confianza", "sentimiento", "guia", "tipo", "capa"}
    assert isinstance(body["reply"], str)
    # Sin LLM_CONECTOR configurado (el default en pruebas), el orquestador
    # nunca escala de verdad al conector -- responde con lo que el ML ya
    # tenía, capa='ml'.
    assert body["capa"] == "ml"


def test_reply_with_empty_text_returns_fallback_with_null_fields(client):
    """Given a POST with a whitespace-only text field.
    When /reply handles it.
    Then it returns the bot's fallback message and null for every other
    field, without needing a real FAQ/sentiment match."""
    import rrhh_api
    resp = client.post("/reply", json={"text": "   "})
    body = resp.get_json()
    assert body["reply"] == rrhh_api.bot.fallback
    assert body["ruta"] is None
    assert body["area"] is None
    assert body["confianza"] is None
    assert body["sentimiento"] is None
    assert body["guia"] is None
    assert body["tipo"] is None
    assert body["capa"] is None


@pytest.mark.parametrize("valor_no_string", [None, 123, ["lista"], {"obj": 1}])
def test_reply_with_a_non_string_text_is_treated_as_empty_instead_of_500(client, valor_no_string):
    """Given a POST where "text" is present but isn't a string (null, a
    number, a list...) -- a malformed client, not an empty field.
    When /reply handles it.
    Then it degrades to the same empty-text fallback branch (200, with
    bot.fallback) instead of raising -- .strip() doesn't exist on those
    types, so calling it unconditionally would 500."""
    resp = client.post("/reply", json={"text": valor_no_string})
    assert resp.status_code == 200
    assert resp.get_json()["ruta"] is None


def test_reply_with_missing_body_is_treated_as_empty_text(client):
    """Given a POST with no JSON body at all.
    When /reply handles it.
    Then it degrades to the same empty-text fallback branch rather than
    raising a 500 (request.get_json(silent=True) returns None, and the `or {}`
    guards the missing .get("text") lookup)."""
    resp = client.post("/reply", content_type="application/json")
    assert resp.status_code == 200
    assert resp.get_json()["ruta"] is None


def test_reply_passes_seguir_through_to_the_orchestrator(client, tmp_path, monkeypatch):
    """Given a low-confidence question and a connector wired to answer, and
    the request includes "seguir": true.
    When /reply handles it.
    Then the orchestrator escalates to the connector (capa='llm') and its
    answer, enriched with what the ML layer already knew, comes back
    through the HTTP contract end to end."""
    import retroalimentacion
    import rrhh_api

    # Esta llamada escala y registra retroalimentación -- aislar RUTA del
    # archivo real, igual que en tests/test_orquestador.py, para no
    # contaminar model/retroalimentacion.json en cada corrida de la suite.
    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")

    rrhh_api.orquestador.conector = type(
        "ConectorDePrueba", (), {"responder": lambda self, pregunta, contexto: "Respuesta generada de prueba."}
    )()
    resp = client.post("/reply", json={"text": "una pregunta que el ml no resuelve con confianza", "seguir": True})
    body = resp.get_json()
    assert body["reply"] == "Respuesta generada de prueba."
    assert body["capa"] == "llm"
    assert body["tipo"] == "generado"


def test_reply_treats_a_falsy_looking_string_in_seguir_as_not_asking_to_continue(client):
    """Given a question the ML layer already answers with confidence
    (an exact registered FAQ phrasing), and "seguir": "false" -- a
    non-empty string, truthy in Python, but clearly meant as "no" by
    whoever sent it.
    When /reply handles it.
    Then it is NOT treated as a request to escalate (capa is not 'llm') --
    bool("false") would wrongly be True; the contract requires the literal
    JSON boolean true."""
    import rrhh_api

    rrhh_api.orquestador.conector = type(
        "ConectorQueNuncaDeberiaLlamarse", (), {"responder": lambda self, pregunta, contexto: "No debería verse."}
    )()
    resp = client.post("/reply", json={"text": "¿Cómo solicito vacaciones?", "seguir": "false"})
    assert resp.get_json()["capa"] != "llm"


def test_reply_response_carries_a_cors_header(client):
    """Given the default local host (RRHH_API_HOST unset, so 127.0.0.1).
    When /reply responds to a cross-origin request.
    Then an Access-Control-Allow-Origin header is present, so the GitHub
    Pages-hosted frontend (a browser) is allowed to read the response."""
    resp = client.post("/reply", json={"text": "hola"},
                        headers={"Origin": "https://hdvergara.github.io"})
    assert "Access-Control-Allow-Origin" in resp.headers


def test_cross_origin_access_never_allows_credentials(client):
    """Given the open origin policy the MVP exception of R11 permits.
    When /reply responds to a cross-origin request.
    Then it does not allow credentials: otherwise any page could use a
    participant's session and void access control."""
    resp = client.post("/reply", json={"text": "hola"}, headers={"Origin": "https://otro.example"})
    assert "Access-Control-Allow-Credentials" not in resp.headers


def test_reply_response_has_no_cors_header_when_containerized(monkeypatch):
    """Given RRHH_API_HOST is set to something other than 127.0.0.1 (the
    containerized case, reachable only from n8n's server-side HTTP Request
    node -- never a browser, which is the only client CORS headers are for).
    When /reply responds to a cross-origin request.
    Then no Access-Control-Allow-Origin header is present: if this instance
    were ever exposed beyond its intended private network by mistake, it
    wouldn't hand out permissive CORS headers a browser could exploit."""
    import rrhh_bot

    monkeypatch.setenv("RRHH_API_HOST", "0.0.0.0")
    sys.modules.pop("rrhh_api", None)
    with patch.object(rrhh_bot, "SentenceTransformer", return_value=FakeSentenceTransformer()), \
         patch.object(rrhh_bot, "pipeline", return_value=FakeSentimentPipeline()):
        import rrhh_api
    client = rrhh_api.app.test_client()

    resp = client.post("/reply", json={"text": "hola"},
                        headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in resp.headers
    sys.modules.pop("rrhh_api", None)
