"""Conector LLM intercambiable (ver CONSTITUTION.md R9): la capa LLM/agéntica
se alcanza siempre a través de esta interfaz, nunca llamando directo a un
backend específico desde model/orquestador.py ni desde las capas anteriores.

Hoy existe una sola implementación real, ConectorMCP, que habla el protocolo
MCP (Model Context Protocol) -- cambiar de backend (Ollama local, el RAG ya
construido en n8n, o un servicio comercial como ChatGPT/Claude/Gemini) es
cambiar a qué servidor MCP apunta, no escribir un cliente HTTP nuevo por cada
uno. No existe todavía un servidor MCP real montado para este proyecto
(ni envolviendo a Ollama ni al RAG de n8n) -- eso es trabajo de
infraestructura del equipo, fuera de este repo; esta clase ya queda lista
para hablarle a cualquiera que exponga la tool esperada.
"""
import os
import shlex
from abc import ABC, abstractmethod


def _partes_comando(comando: str) -> list:
    """shlex.split, no str.split: MCP_SERVIDOR_CMD puede traer un argumento
    entre comillas con espacios adentro (p. ej. 'servidor --config "ruta
    con espacios"') -- split() partiría eso por cada espacio, no solo entre
    argumentos reales. shlex usa reglas de shell POSIX (la barra invertida
    escapa, no es un separador de ruta) -- en Windows, evitar barras
    invertidas sin comillas en MCP_SERVIDOR_CMD; usar barras normales o
    comillas si el comando las necesita."""
    return shlex.split(comando)


class ConectorLLM(ABC):
    """Una respuesta en texto, o None si no hay respuesta disponible (sin
    servidor configurado, error de conexión, o la tool no supo responder).
    Nunca lanza -- un conector LLM inalcanzable debe caer con gracia al
    resultado que la capa ML ya tenía, igual que el resto de la cadena."""

    @abstractmethod
    def responder(self, pregunta: str, contexto: dict) -> str | None:
        ...


class ConectorNulo(ConectorLLM):
    """Default cuando no hay LLM_CONECTOR configurado -- nunca responde,
    así que el orquestador siempre cae de vuelta a la capa ML."""

    def responder(self, pregunta: str, contexto: dict) -> str | None:
        return None


class ConectorMCP(ConectorLLM):
    """Cliente MCP: se conecta a un servidor configurado por variables de
    entorno y le pide que responda la pregunta, pasándole el contexto
    (ruta/area) que la capa ML ya calculó, como argumentos de la tool."""

    def __init__(self):
        self.comando = os.environ.get("MCP_SERVIDOR_CMD")
        self.url = os.environ.get("MCP_SERVIDOR_URL")
        self.herramienta = os.environ.get("MCP_HERRAMIENTA", "responder_rrhh")

    def responder(self, pregunta: str, contexto: dict) -> str | None:
        if not self.comando and not self.url:
            return None
        try:
            return self._responder_mcp(pregunta, contexto)
        except Exception:
            return None

    def _responder_mcp(self, pregunta: str, contexto: dict) -> str | None:
        import asyncio

        async def _llamar():
            from mcp import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client

            if self.comando:
                partes = _partes_comando(self.comando)
                if not partes:
                    return None
                params = StdioServerParameters(command=partes[0], args=partes[1:])
                transporte = stdio_client(params)
            else:
                from mcp.client.sse import sse_client

                transporte = sse_client(self.url)

            async with transporte as (lectura, escritura):
                async with ClientSession(lectura, escritura) as sesion:
                    await sesion.initialize()
                    resultado = await sesion.call_tool(
                        self.herramienta, {"pregunta": pregunta, "contexto": contexto}
                    )
                    if not resultado.content:
                        return None
                    return "".join(
                        bloque.text for bloque in resultado.content if hasattr(bloque, "text")
                    ) or None

        return asyncio.run(_llamar())


def crear_conector() -> ConectorLLM:
    modo = os.environ.get("LLM_CONECTOR", "ninguno")
    if modo == "mcp":
        return ConectorMCP()
    return ConectorNulo()
