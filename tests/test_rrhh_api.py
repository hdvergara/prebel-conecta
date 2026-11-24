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
    Then the response is 200 JSON with exactly the five documented keys."""
    resp = client.post("/reply", json={"text": "hola"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {"reply", "ruta", "area", "confianza", "sentimiento"}
    assert isinstance(body["reply"], str)


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


def test_reply_with_missing_body_is_treated_as_empty_text(client):
    """Given a POST with no JSON body at all.
    When /reply handles it.
    Then it degrades to the same empty-text fallback branch rather than
    raising a 500 (request.get_json(silent=True) returns None, and the `or {}`
    guards the missing .get("text") lookup)."""
    resp = client.post("/reply", content_type="application/json")
    assert resp.status_code == 200
    assert resp.get_json()["ruta"] is None


def test_reply_response_carries_a_cors_header(client):
    """Given the default local host (RRHH_API_HOST unset, so 127.0.0.1).
    When /reply responds to a cross-origin request.
    Then an Access-Control-Allow-Origin header is present, so the GitHub
    Pages-hosted frontend (a browser) is allowed to read the response."""
    resp = client.post("/reply", json={"text": "hola"},
                        headers={"Origin": "https://hdvergara.github.io"})
    assert "Access-Control-Allow-Origin" in resp.headers


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
