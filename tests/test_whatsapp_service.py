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


# Context: basic sender identification (CONSTITUTION.md R7 -- by WhatsApp
# number only, never a substitute for real authentication), against the real
# model/empleados_mock.json content (harmless to load; only the ML models are faked).

def test_buscar_persona_por_telefono_matches_regardless_of_formatting(servicio):
    """Given a WhatsApp sender id as plain digits (573005550104).
    When compared against empleados_mock.json's telefono field, which is
    formatted with spaces and a leading '+' ("+57 300 555 0104").
    Then it still matches, by digits only."""
    persona = servicio.buscar_persona_por_telefono("573005550104")
    assert persona["primer_nombre"] == "Andrés"


def test_buscar_persona_por_telefono_returns_none_for_an_unknown_number(servicio):
    """Given a WhatsApp sender id that matches no mock employee's telefono.
    When buscar_persona_por_telefono() is called.
    Then it returns None rather than guessing a persona."""
    assert servicio.buscar_persona_por_telefono("573001112233") is None


def test_parece_numero_documento_accepts_plain_digit_strings_in_range(servicio):
    """Given a message that is only digits, 6 to 12 of them.
    When parece_numero_documento() is called.
    Then it's treated as a self-identification attempt."""
    assert servicio.parece_numero_documento("1000000001") is True


@pytest.mark.parametrize("texto", ["hola", "1000000001 porfa", "123", "1234567890123", ""])
def test_parece_numero_documento_rejects_anything_else(servicio, texto):
    """Given a message that isn't a bare 6-12 digit string (a real question,
    digits with extra words, too short, too long, or empty).
    When parece_numero_documento() is called.
    Then it's NOT treated as a self-identification attempt -- a real
    question must still reach RRHHBot, not get swallowed as a bad document
    number."""
    assert servicio.parece_numero_documento(texto) is False


def test_buscar_persona_por_documento_matches_a_known_mock_employee(servicio):
    """Given one of the 4 fictitious numero_documento values.
    When buscar_persona_por_documento() is called.
    Then it returns that employee."""
    persona = servicio.buscar_persona_por_documento("1000000003")
    assert persona["primer_nombre"] == "Camila"


def test_buscar_persona_por_documento_returns_none_for_an_unknown_number(servicio):
    assert servicio.buscar_persona_por_documento("9999999999") is None


def test_identifying_by_documento_is_remembered_for_the_rest_of_the_session(client, servicio):
    """Given a message from an unrecognized phone number (like the
    emulator's own default test contact) that is just a known
    numero_documento.
    When /webhook handles it, and then a real question arrives from the same
    sender.
    Then the first message gets a confirmation (not routed through
    RRHHBot), and the second gets personalized data -- the self-reported
    identification is remembered in-memory for that sender for the rest of
    this run (CONSTITUTION.md R7: still not authentication)."""
    remitente = "573001112233"  # no coincide con ningún teléfono ficticio

    doc_body = {"entry": [{"changes": [{"value": {"messages": [
        {"id": "wamid.8", "from": remitente, "type": "text", "text": {"body": "1000000003"}},
    ]}}]}]}
    raw_doc = json.dumps(doc_body).encode("utf-8")
    fake_response = MagicMock(ok=True, content=b"{}")
    fake_response.json.return_value = {}
    with patch("whatsapp_service.requests.post", return_value=fake_response) as post, \
         patch.object(servicio.bot, "match") as match_mock:
        resp = client.post("/webhook", data=raw_doc, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw_doc),
        })
        match_mock.assert_not_called()  # un número de documento no es una pregunta
    assert resp.status_code == 200
    _read_call, reply_call = post.call_args_list
    assert "Camila" in reply_call.kwargs["json"]["text"]["body"]

    pregunta_body = {"entry": [{"changes": [{"value": {"messages": [
        {"id": "wamid.9", "from": remitente, "type": "text", "text": {"body": "cuantos dias de vacaciones tengo"}},
    ]}}]}]}
    raw_pregunta = json.dumps(pregunta_body).encode("utf-8")
    with patch("whatsapp_service.requests.post", return_value=fake_response) as post, \
         patch.object(servicio.bot, "match", return_value={
             "respuesta": "Tu saldo de vacaciones aparece en tu perfil, en Mi espacio.",
             "ruta": "vacaciones", "area": "gh", "confianza": 1.0,
             "sentimiento": {"etiqueta": "neutral", "estrellas": 3, "confianza": 0.5},
             "guia": "Pide tus vacaciones con anticipación.",
         }):
        resp = client.post("/webhook", data=raw_pregunta, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw_pregunta),
        })
    assert resp.status_code == 200
    _read_call, reply_call = post.call_args_list
    texto = reply_call.kwargs["json"]["text"]["body"]
    assert "*6* días hábiles de vacaciones acumulados" in texto  # Camila


def test_identifying_by_an_unknown_documento_gives_an_error_not_a_crash(client, servicio):
    """Given a bare digit-string message that matches no mock employee.
    When /webhook handles it.
    Then it answers with an error, not an invented identity, and RRHHBot is
    never consulted for what is clearly not a question."""
    body = {"entry": [{"changes": [{"value": {"messages": [
        {"id": "wamid.10", "from": "573001112233", "type": "text", "text": {"body": "9999999999"}},
    ]}}]}]}
    raw = json.dumps(body).encode("utf-8")
    fake_response = MagicMock(ok=True, content=b"{}")
    fake_response.json.return_value = {}
    with patch("whatsapp_service.requests.post", return_value=fake_response) as post, \
         patch.object(servicio.bot, "match") as match_mock:
        resp = client.post("/webhook", data=raw, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw),
        })
        match_mock.assert_not_called()
    assert resp.status_code == 200
    _read_call, reply_call = post.call_args_list
    assert "No encontré" in reply_call.kwargs["json"]["text"]["body"]


def test_personalizar_leads_with_the_real_value_then_the_guia_for_a_route_with_basic_data(servicio):
    """Given a known persona and a match whose ruta has a mapped field
    (vacaciones) and a 'guia' (the actionable step, without the generic
    "revisa tu perfil" referral already baked into match['respuesta']).
    When personalizar() is called.
    Then the real value leads the response, the guia follows it, the
    original generic respuesta text is NOT reused (it would be redundant
    once the real number is already stated), and there's an explicit note
    that this identification is basic, not verified -- per R7."""
    persona = servicio.buscar_persona_por_telefono("573005550101")  # Valentina, 12 días
    match = {"respuesta": "Texto genérico con remisión a tu perfil.", "ruta": "vacaciones",
              "guia": "Pide tus vacaciones a tu jefe con anticipación."}
    resultado = servicio.personalizar(match, persona)
    # *12* en negrilla (formato nativo de WhatsApp) para que el dato resalte.
    assert resultado.startswith("Valentina, tienes *12* días hábiles de vacaciones acumulados.")
    assert "Pide tus vacaciones a tu jefe con anticipación." in resultado
    assert "tu perfil" not in resultado
    assert "Identificación básica" in resultado


def test_personalizar_invites_self_identification_by_documento_without_a_matched_persona(servicio):
    """Given no persona was identified (unknown sender) and a ruta that does
    have basic data mapped.
    When personalizar() is called.
    Then instead of silently repeating only the generic respuesta forever
    (the original bug: the same canned text for every follow-up question),
    it also invites the person to self-identify by número de documento, so a
    WhatsApp number that isn't one of the fictitious ones can still get real
    data on their very next message."""
    match = {"respuesta": "Texto genérico.", "ruta": "vacaciones", "guia": "Guía."}
    resultado = servicio.personalizar(match, None)
    assert resultado.startswith("Texto genérico.")
    assert "número de documento" in resultado


def test_personalizar_leaves_response_untouched_for_a_route_without_basic_data(servicio):
    """Given a known persona but a ruta with no entry in
    DATOS_BASICOS_POR_RUTA (e.g. certificado -- there's no single mock field
    that answers it).
    When personalizar() is called.
    Then the original generic response text comes back unchanged."""
    persona = servicio.buscar_persona_por_telefono("573005550101")
    match = {"respuesta": "Texto genérico.", "ruta": "certificado", "guia": None}
    assert servicio.personalizar(match, persona) == "Texto genérico."


def test_identified_sender_gets_a_personalized_basic_data_value_in_the_reply(client, servicio):
    """Given an incoming message from a phone number that matches Valentina's
    mock telefono, and a match whose ruta is 'vacaciones' with a 'guia'.
    When /webhook handles it end to end.
    Then the reply sent back leads with her real vacation balance and the
    guia, dropping the generic "revisa tu perfil" referral (now redundant --
    the real number was just given directly)."""
    body = {
        "entry": [{"changes": [{"value": {"messages": [
            {"id": "wamid.6", "from": "573005550101", "type": "text", "text": {"body": "cuantos dias de vacaciones tengo"}},
        ]}}]}],
    }
    raw = json.dumps(body).encode("utf-8")
    fake_response = MagicMock(ok=True, content=b"{}")
    fake_response.json.return_value = {}
    with patch("whatsapp_service.requests.post", return_value=fake_response) as post, \
         patch.object(servicio.bot, "match", return_value={
             "respuesta": "Tu saldo de vacaciones aparece en tu perfil, en Mi espacio.",
             "ruta": "vacaciones", "area": "gh", "confianza": 1.0,
             "sentimiento": {"etiqueta": "neutral", "estrellas": 3, "confianza": 0.5},
             "guia": "Pide tus vacaciones a tu jefe con anticipación.",
         }):
        resp = client.post("/webhook", data=raw, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw),
        })
    assert resp.status_code == 200
    _read_call, reply_call = post.call_args_list
    texto = reply_call.kwargs["json"]["text"]["body"]
    assert "*12* días hábiles de vacaciones acumulados" in texto
    assert "Pide tus vacaciones a tu jefe con anticipación." in texto
    assert "tu perfil" not in texto


def test_unidentified_sender_gets_the_match_plus_a_self_identification_invite(client, servicio):
    """Given an incoming message from a phone number that matches no mock
    employee, with a ruta that has basic data mapped.
    When /webhook handles it end to end.
    Then the reply keeps RRHHBot's own text and appends an invite to
    self-identify by número de documento -- not a repeat of the exact same
    unhelpful text on every follow-up (the original bug report)."""
    body = {
        "entry": [{"changes": [{"value": {"messages": [
            {"id": "wamid.7", "from": "573009999999", "type": "text", "text": {"body": "cuantos dias de vacaciones tengo"}},
        ]}}]}],
    }
    raw = json.dumps(body).encode("utf-8")
    fake_response = MagicMock(ok=True, content=b"{}")
    fake_response.json.return_value = {}
    respuesta_bot = "Tu saldo de vacaciones aparece en tu perfil, en Mi espacio."
    with patch("whatsapp_service.requests.post", return_value=fake_response) as post, \
         patch.object(servicio.bot, "match", return_value={
             "respuesta": respuesta_bot, "ruta": "vacaciones", "area": "gh", "confianza": 1.0,
             "sentimiento": {"etiqueta": "neutral", "estrellas": 3, "confianza": 0.5},
         }):
        resp = client.post("/webhook", data=raw, headers={
            "Content-Type": "application/json", "X-Hub-Signature-256": _firmar(raw),
        })
    assert resp.status_code == 200
    _read_call, reply_call = post.call_args_list
    texto = reply_call.kwargs["json"]["text"]["body"]
    assert texto.startswith(respuesta_bot)
    assert "número de documento" in texto
