"""API local del bot de RRHH, para correr en tu máquina y ser llamada
desde dist/app.js (fetch a http://127.0.0.1:5000/reply).

Si esta API no está corriendo, app.js sigue funcionando con su propio
buscador en JavaScript sobre faq.js; esta API solo añade respuestas por
similitud semántica cuando está disponible.

Uso (PowerShell):
    pip install -r requirements.txt
    python model/rrhh_api.py
"""
from flask import Flask, jsonify, request
from flask_cors import CORS

from rrhh_bot import RRHHBot

app = Flask(__name__)
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
    app.run(host="127.0.0.1", port=5000)
