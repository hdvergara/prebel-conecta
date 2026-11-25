"""Unit tests for model/conectores.py.

No se conecta a un servidor MCP real (no hay uno disponible en esta
máquina) -- se prueba el contrato de ConectorLLM (nunca lanza, devuelve
None si no hay nada que responder) parcheando el método privado que de
verdad hablaría el protocolo. La conexión en vivo necesita el entorno del
equipo, igual que ya pasó con n8n/Ollama en PRs anteriores.
"""
from unittest.mock import patch

import pytest

from conectores import ConectorMCP, ConectorNulo, _partes_comando, crear_conector


def test_conector_nulo_never_answers():
    """Given ConectorNulo (el default sin LLM_CONECTOR configurado).
    When responder() se llama.
    Then siempre devuelve None, para que el orquestador caiga de vuelta a
    la capa ML."""
    assert ConectorNulo().responder("cualquier pregunta", {}) is None


def test_crear_conector_defaults_to_nulo_without_llm_conector_env(monkeypatch):
    """Given LLM_CONECTOR sin definir.
    When crear_conector() se llama.
    Then devuelve un ConectorNulo."""
    monkeypatch.delenv("LLM_CONECTOR", raising=False)
    assert isinstance(crear_conector(), ConectorNulo)


def test_crear_conector_returns_mcp_when_configured(monkeypatch):
    """Given LLM_CONECTOR=mcp.
    When crear_conector() se llama.
    Then devuelve un ConectorMCP."""
    monkeypatch.setenv("LLM_CONECTOR", "mcp")
    assert isinstance(crear_conector(), ConectorMCP)


def test_conector_mcp_without_server_configured_returns_none(monkeypatch):
    """Given ConectorMCP sin MCP_SERVIDOR_CMD ni MCP_SERVIDOR_URL.
    When responder() se llama.
    Then devuelve None sin intentar conectarse a nada."""
    monkeypatch.delenv("MCP_SERVIDOR_CMD", raising=False)
    monkeypatch.delenv("MCP_SERVIDOR_URL", raising=False)
    assert ConectorMCP().responder("una pregunta", {}) is None


def test_conector_mcp_returns_the_tool_response_text(monkeypatch):
    """Given un servidor configurado (MCP_SERVIDOR_CMD) y una llamada MCP
    que, de responder, devolvería un texto.
    When responder() se llama.
    Then ese texto es lo que se devuelve."""
    monkeypatch.setenv("MCP_SERVIDOR_CMD", "servidor-de-prueba")
    conector = ConectorMCP()
    with patch.object(conector, "_responder_mcp", return_value="Respuesta de la tool MCP."):
        assert conector.responder("una pregunta", {"ruta": "x"}) == "Respuesta de la tool MCP."


def test_partes_comando_respects_quoted_arguments_with_spaces():
    """Given a command string with a quoted argument that contains spaces.
    When _partes_comando() splits it.
    Then the quoted argument stays as one piece, not split()'s one-per-space
    (the exact bug a plain str.split() would have had: a path or flag value
    with spaces breaking into several, wrong arguments)."""
    assert _partes_comando('servidor --config "ruta con espacios"') == ["servidor", "--config", "ruta con espacios"]


def test_conector_mcp_with_a_blank_command_returns_none(monkeypatch):
    """Given MCP_SERVIDOR_CMD set to whitespace only.
    When responder() se llama.
    Then devuelve None en vez de intentar ejecutar un comando vacío."""
    monkeypatch.setenv("MCP_SERVIDOR_CMD", "   ")
    assert ConectorMCP().responder("una pregunta", {}) is None


def test_conector_mcp_never_raises_on_connection_errors(monkeypatch):
    """Given un servidor configurado, pero la conexión MCP falla (servidor
    caído, tool inexistente, lo que sea).
    When responder() se llama.
    Then devuelve None en vez de propagar la excepción -- un conector LLM
    inalcanzable debe caer con gracia, igual que el resto de la cadena."""
    monkeypatch.setenv("MCP_SERVIDOR_CMD", "servidor-de-prueba")
    conector = ConectorMCP()
    with patch.object(conector, "_responder_mcp", side_effect=ConnectionError("servidor no disponible")):
        assert conector.responder("una pregunta", {}) is None
