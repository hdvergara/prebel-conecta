"""Unit tests for the WhatsApp channel's webhook contract and dispatch logic.

Per CONSTITUTION.md "Harness": the real ML models are faked (fakes.py) and
every outbound HTTP call (requests.post, the one that would hit the emulator
or real Meta) is mocked -- these tests run offline, with no network and no
real WhatsApp-compatible server involved. RRHHBot's own matching logic is
covered by test_rrhh_bot.py, so it isn't re-verified here; this suite only
checks that whatsapp_service.py wires webhook verification, signature
validation, and message dispatch correctly.
"""
import hashlib
import hmac
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from fakes import FakeSentenceTransformer, FakeSentimentPipeline

APP_SECRET = "test-secret-for-unit-tests"


def _firmar(cuerpo: bytes) -> str:
    return "sha256=" + hmac.new(APP_SECRET.encode("utf-8"), cuerpo, hashlib.sha256).hexdigest()


@pytest.fixture
def servicio():
    """Fresh module per test, with RRHHBot's heavy models faked and
    WA_APP_SECRET/WA_VERIFY_TOKEN pinned to known values, re-imported inside
    the patch context so its module-level `bot = RRHHBot()` runs against the
    fakes rather than the real ~1GB models."""
    import rrhh_bot

    sys.modules.pop("whatsapp_service", None)
    with patch.object(rrhh_bot, "SentenceTransformer", return_value=FakeSentenceTransformer()), \
         patch.object(rrhh_bot, "pipeline", return_value=FakeSentimentPipeline({"hola": ("5 stars", 0.8)})), \
         patch.dict("os.environ", {"WA_APP_SECRET": APP_SECRET, "WA_VERIFY_TOKEN": "verificame"}):
        import whatsapp_service

    yield whatsapp_service
    sys.modules.pop("whatsapp_service", None)


@pytest.fixture
def client(servicio):
    return servicio.app.test_client()


# Context: a fresh Flask test client per test, against the real
# model/faq_rrhh.json content (harmless -- only the ML models are faked).

def test_webhook_verification_echoes_challenge_when_token_matches(client):
    """Given a GET with hub.mode=subscribe and the configured verify token.
    When /webhook handles it.
    Then it answers 200 with hub.challenge as the raw body (what Meta and the
    emulator require to complete a webhook subscription)."""
    resp = client.get("/webhook", query_string={
        "hub.mode": "subscribe", "hub.verify_token": "verificame", "hub.challenge": "abc123",
    })
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "abc123"


def test_webhook_verification_rejects_wrong_token(client):
    """Given a GET with a verify token that does not match WA_VERIFY_TOKEN.
    When /webhook handles it.
    Then it answers 403, without echoing the challenge."""
    resp = client.get("/webhook", query_string={
        "hub.mode": "subscribe", "hub.verify_token": "intruso", "hub.challenge": "abc123",
    })
    assert resp.status_code == 403


def test_incoming_message_with_invalid_signature_is_rejected(client):
    """Given a POST whose X-Hub-Signature-256 does not match the body.
    When /webhook handles it.
    Then it answers 401 and never reaches message dispatch (no outbound call)."""
    with patch("whatsapp_service.requests.post") as post:
        resp = client.post("/webhook", data=b"{}", headers={"X-Hub-Signature-256": "sha256=0000"})
        assert resp.status_code == 401
        post.assert_not_called()


def test_incoming_text_message_is_answered_via_rrhhbot(client, servicio):
    """Given a correctly signed webhook delivery with one incoming text message.
    When /webhook handles it.
    Then it marks the message read and sends back RRHHBot's matched answer to
    the sender, both via a POST to the configured Graph-compatible messages URL."""
    body = {
        "entry": [{"changes": [{"value": {"messages": [
            {"id": "wamid.1", "from": "573001112233", "type": "text", "text": {"body": "hola"}},
        ]}}]}],
    }
    raw = json.dumps(body).encode("utf-8")
    fake_response = MagicMock(ok=True, content=b"{}")
    fake_response.json.return_value = {}
    with patch("whatsapp_service.requests.post", return_value=fake_response) as post, \
         patch.object(servicio.bot, "match", return_value={
             "respuesta": "Respuesta de prueba", "ruta": None, "area": None,
             "confianza": 1.0, "sentimiento": {"etiqueta": "positivo", "estrellas": 5, "confianza": 0.8},
         }):
        resp = client.post("/webhook", data=raw, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw),
        })
    assert resp.status_code == 200
    assert post.call_count == 2  # marcar_leido + responder_texto
    read_call, reply_call = post.call_args_list
    assert read_call.kwargs["json"]["status"] == "read"
    assert read_call.kwargs["json"]["message_id"] == "wamid.1"
    assert reply_call.kwargs["json"]["to"] == "573001112233"
    assert reply_call.kwargs["json"]["text"]["body"] == "Respuesta de prueba"
    assert reply_call.kwargs["headers"]["Authorization"].startswith("Bearer ")


def test_incoming_non_text_message_gets_a_static_notice_instead_of_crashing(client):
    """Given a signed delivery whose message type is not 'text' (e.g. image).
    When /webhook handles it.
    Then it still marks it read and replies with a static "text only" notice,
    rather than raising on a missing msg['text'] key."""
    body = {
        "entry": [{"changes": [{"value": {"messages": [
            {"id": "wamid.2", "from": "573001112233", "type": "image", "image": {"id": "media1"}},
        ]}}]}],
    }
    raw = json.dumps(body).encode("utf-8")
    fake_response = MagicMock(ok=True, content=b"{}")
    fake_response.json.return_value = {}
    with patch("whatsapp_service.requests.post", return_value=fake_response) as post:
        resp = client.post("/webhook", data=raw, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw),
        })
    assert resp.status_code == 200
    _read_call, reply_call = post.call_args_list
    assert "texto" in reply_call.kwargs["json"]["text"]["body"]


def test_a_failing_outbound_send_does_not_break_the_webhook_response(client):
    """Given the Graph-compatible endpoint is unreachable (requests.post raises).
    When /webhook processes an incoming message.
    Then the exception is caught and logged per message, and /webhook still
    answers 200 overall (Meta/the emulator must not see a 5xx and retry forever)."""
    body = {
        "entry": [{"changes": [{"value": {"messages": [
            {"id": "wamid.3", "from": "573001112233", "type": "text", "text": {"body": "hola"}},
        ]}}]}],
    }
    raw = json.dumps(body).encode("utf-8")
    with patch("whatsapp_service.requests.post", side_effect=ConnectionError("sin red")):
        resp = client.post("/webhook", data=raw, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw),
        })
    assert resp.status_code == 200
