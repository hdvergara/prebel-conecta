"""API local del bot de RRHH, para correr en tu máquina y ser llamada
desde dist/app.js (fetch a http://127.0.0.1:5000/reply).

Si esta API no está corriendo, app.js sigue funcionando con su propio
buscador en JavaScript sobre faq.js; esta API solo añade respuestas por
similitud semántica cuando está disponible.

También la llama, por su cuenta, el Cerebro de n8n (ver n8n/README.md)
como primer intento (Tier 1, "ML") antes de su propio RAG+LLM (Tier 2,
"Agentic") -- para eso corre contenerizada en el servidor del equipo
(ver Dockerfile), nunca expuesta públicamente: solo n8n, en la misma red
privada, le habla. RRHH_API_HOST controla a qué dirección se enlaza;
por defecto sigue siendo 127.0.0.1 (uso local, sin cambios) y el
contenedor lo cambia a 0.0.0.0.

Uso (PowerShell):
    pip install -r requirements.txt
    python model/rrhh_api.py
"""
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from rrhh_bot import RRHHBot

app = Flask(__name__)
RRHH_API_HOST = os.environ.get("RRHH_API_HOST", "127.0.0.1")
# CORS solo hace falta para el caso local: dist/app.js corre en el
# navegador del visitante y necesita el encabezado para leer la respuesta
# entre orígenes. El Cerebro de n8n (Tier 1) es un llamador del lado del
# servidor, no un navegador -- no respeta ni necesita CORS. Por eso solo se
# habilita cuando esta instancia escucha en 127.0.0.1 (el caso de siempre):
# si corre contenerizada (RRHH_API_HOST=0.0.0.0), queda apagado, para que
# nunca emita encabezados CORS permisivos si alguna vez quedara expuesta
# por error más allá de la red privada que le indica n8n/README.md.
if RRHH_API_HOST == "127.0.0.1":
    CORS(app)
bot = RRHHBot()


@app.post("/reply")
def reply():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify(reply=bot.fallback, ruta=None, area=None, confianza=None, sentimiento=None)
    match = bot.match(text)
    return jsonify(
        reply=match["respuesta"], ruta=match["ruta"], area=match["area"],
        confianza=match["confianza"], sentimiento=match["sentimiento"],
    )


if __name__ == "__main__":
    app.run(host=RRHH_API_HOST, port=5000)
