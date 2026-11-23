"""Canal de WhatsApp para el bot de RRHH: recibe los webhooks de mensajes
entrantes desde un entorno compatible con la WhatsApp Cloud API (el emulador
local en ../whatsapp-emulator, fuera de este repo; o Meta real más adelante),
los pasa por RRHHBot -- el mismo modelo que model/rrhh_api.py expone al
navegador -- y responde llamando de vuelta a esa API tipo Graph.

No reemplaza rrhh_api.py (esa sigue sirviendo a dist/app.js por fetch); este
es un canal independiente para probar la misma lógica por WhatsApp.

Los parámetros de conexión y secretos (ver .env.example) se leen de variables
de entorno; nunca van hardcodeados ni se commitean. Por defecto apuntan al
emulador local. Para apuntar a un entorno de pruebas real de Meta más
adelante, solo hay que cambiar esas variables -- no el código.

Uso (PowerShell, con el emulador ya corriendo en :4010):
    pip install -r requirements.txt
    python model/whatsapp_service.py
"""
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path

import requests
from flask import Flask, jsonify, request

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass  # python-dotenv es opcional; sin él, solo se leen variables ya exportadas

from rrhh_bot import RRHHBot

GRAPH_URL = os.environ.get("WA_GRAPH_URL", "http://localhost:4010")
API_VERSION = os.environ.get("WA_API_VERSION", "v26.0")
PHONE_NUMBER_ID = os.environ.get("WA_PHONE_NUMBER_ID", "100000000000001")
ACCESS_TOKEN = os.environ.get("WA_ACCESS_TOKEN", "local-dev-token")
VERIFY_TOKEN = os.environ.get("WA_VERIFY_TOKEN", "prebel-conecta-dev")
APP_SECRET = os.environ.get("WA_APP_SECRET", "prebel-conecta-dev-secret")
SERVICE_PORT = int(os.environ.get("WA_SERVICE_PORT", "3000"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("whatsapp_service")

app = Flask(__name__)
bot = RRHHBot()

EMPLEADOS = json.loads((Path(__file__).resolve().parent / "empleados_mock.json").read_text(encoding="utf-8"))["empleados"]

# Qué dato básico puede devolver cada ruta, una vez identificado el remitente
# por su número de WhatsApp -- ver CONSTITUTION.md R7: esto es identificación
# básica (por número), no autenticación. MFA/confianza queda para más adelante.
DATOS_BASICOS_POR_RUTA = {
    "vacaciones": ("dias_vacaciones_acumulados", "días hábiles de vacaciones acumulados"),
    "prima": ("dias_prima_acumulados", "días de prima acumulados este semestre"),
}


def _solo_digitos(texto: str) -> str:
    return "".join(c for c in (texto or "") if c.isdigit())


def buscar_persona_por_telefono(numero_whatsapp: str) -> dict | None:
    """Identificación básica, NO autenticación: empareja el número de
    WhatsApp del remitente contra el teléfono ficticio de
    empleados_mock.json. Cualquiera que escriba desde ese número ve ese dato
    -- suficiente para la demo, pero no un sustituto de un factor real de
    verificación (MFA/confianza, ver CONSTITUTION.md R7)."""
    objetivo = _solo_digitos(numero_whatsapp)
    if not objetivo:
        return None
    for persona in EMPLEADOS:
        if _solo_digitos(persona["telefono"]) == objetivo:
            return persona
    return None


def personalizar(match: dict, persona: dict | None) -> str:
    """Si el remitente quedó identificado por teléfono y la ruta tiene un
    dato básico mapeado, responde con el valor real primero y la guía
    accionable (match["guia"], sin la frase que remite a "revisa tu perfil")
    después -- el dato y el siguiente paso, nada más. Sin persona o sin dato
    para esa ruta, se usa tal cual la respuesta genérica del FAQ (la que sí
    incluye esa remisión, para quien no pudo identificarse)."""
    campo = DATOS_BASICOS_POR_RUTA.get(match["ruta"])
    if not campo or not persona:
        return match["respuesta"]
    atributo, etiqueta = campo
    valor = persona.get(atributo)
    if valor is None:
        return match["respuesta"]
    partes = [f"{persona['primer_nombre']}, tienes {valor} {etiqueta}."]
    if match.get("guia"):
        partes.append(match["guia"])
    partes.append("(Identificación básica por tu número de WhatsApp, sin verificación adicional todavía.)")
    return " ".join(partes)


def _messages_url() -> str:
    return f"{GRAPH_URL}/{API_VERSION}/{PHONE_NUMBER_ID}/messages"


def enviar(payload: dict) -> dict:
    """POSTea un mensaje saliente (o un 'read') a la API tipo Graph."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    body = {"messaging_product": "whatsapp", **payload}
    resp = requests.post(_messages_url(), json=body, headers=headers, timeout=10)
    if not resp.ok:
        log.error("Error enviando a WhatsApp (%s): %s", resp.status_code, resp.text)
    return resp.json() if resp.content else {}


def responder_texto(to: str, texto: str) -> dict:
    return enviar({"to": to, "type": "text", "text": {"body": texto}})


def marcar_leido(message_id: str) -> dict:
    return enviar({"status": "read", "message_id": message_id})


def firma_valida(cuerpo_crudo: bytes, encabezado: str) -> bool:
    """Valida X-Hub-Signature-256 (HMAC-SHA256 del cuerpo crudo con
    WA_APP_SECRET) -- lo mismo que exige Meta y que imita el emulador."""
    if not encabezado:
        return False
    esperado = "sha256=" + hmac.new(APP_SECRET.encode("utf-8"), cuerpo_crudo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, encabezado)


def procesar_mensaje(msg: dict) -> None:
    """Responde un mensaje entrante usando RRHHBot. Solo texto por ahora --
    otros tipos (imagen, audio, interactivo...) reciben un aviso en vez de
    fallar en silencio."""
    marcar_leido(msg["id"])
    remitente = msg.get("from")
    if msg.get("type") != "text":
        responder_texto(remitente, "Por ahora solo puedo leer mensajes de texto. Escribe tu pregunta de RRHH.")
        return
    texto = msg["text"]["body"]
    match = bot.match(texto)
    persona = buscar_persona_por_telefono(remitente)
    responder_texto(remitente, personalizar(match, persona))


@app.get("/webhook")
def verificar_webhook():
    """Paso 1 de la suscripción al webhook: quien lo configura (Meta o el
    emulador) llama GET con hub.verify_token y espera hub.challenge de vuelta
    si coincide con WA_VERIFY_TOKEN."""
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")
    if modo == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token de verificación inválido", 403


@app.post("/webhook")
def recibir_webhook():
    """Paso 2: entregas de mensajes/estados. Valida la firma antes de
    confiar en el contenido; cada mensaje de texto entrante se contesta con
    RRHHBot."""
    raw = request.get_data()
    if not firma_valida(raw, request.headers.get("X-Hub-Signature-256", "")):
        log.warning("Firma inválida en una entrega de webhook; se descarta")
        return jsonify(error="firma inválida"), 401
    body = request.get_json(silent=True) or {}
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            valor = change.get("value", {})
            for msg in valor.get("messages", []):
                try:
                    procesar_mensaje(msg)
                except Exception:
                    log.exception("Error procesando el mensaje %s", msg.get("id"))
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    log.info("Canal WhatsApp escuchando en http://localhost:%s/webhook (envía a %s)", SERVICE_PORT, _messages_url())
    app.run(host="0.0.0.0", port=SERVICE_PORT)
