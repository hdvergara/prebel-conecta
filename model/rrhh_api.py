"""API local del bot de RRHH, para correr en tu máquina y ser llamada
desde dist/app.js (fetch a http://127.0.0.1:5000/reply).

Si esta API no está corriendo, app.js sigue funcionando con su propio
buscador en JavaScript sobre faq.js; esta API solo añade respuestas por
similitud semántica cuando está disponible.

Desde la "reducción primaria del modelo" (ver REDUCCION_PRIMARIA_DEL_MODELO.md
y CONSTITUTION.md R8/R9), /reply ya no solo expone el match del ML: pasa por
model/orquestador.py, que decide con los umbrales de model/arquitectura.json
si responder con eso o escalar al conector LLM (model/conectores.py). Sin
LLM_CONECTOR configurado (el default), nunca escala -- se comporta
exactamente como antes, una consulta rápida sin red externa.

El Cerebro de n8n (ver n8n/README.md) sigue llamando a este mismo endpoint
como su propio Tier 1, sin cambios en este branch. Si en esta misma
instancia se configura LLM_CONECTOR, esa llamada de n8n hereda la latencia
de la escalada -- si se quiere mantener el Tier 1 de n8n instantáneo,
conviene correr esa instancia sin LLM_CONECTOR y reservar la escalada para
la que atiende al portal/otros llamadores directos.

Para eso corre contenerizada en el servidor del equipo (ver Dockerfile),
nunca expuesta públicamente: solo n8n, en la misma red privada, le habla.
RRHH_API_HOST controla a qué dirección se enlaza; por defecto sigue siendo
127.0.0.1 (uso local, sin cambios) y el contenedor lo cambia a 0.0.0.0.

Uso (PowerShell):
    pip install -r requirements.txt
    python model/rrhh_api.py
"""
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from orquestador import Orquestador
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
orquestador = Orquestador(bot)


@app.post("/reply")
def reply():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "")
    text = text.strip() if isinstance(text, str) else ""
    if not text:
        return jsonify(reply=bot.fallback, ruta=None, area=None, confianza=None,
                        sentimiento=None, guia=None, tipo=None, capa=None)
    resultado = orquestador.responder_pregunta(text, pedir_continuar=body.get("seguir") is True)
    return jsonify(
        reply=resultado["respuesta"], ruta=resultado["ruta"], area=resultado["area"],
        confianza=resultado["confianza"], sentimiento=resultado["sentimiento"],
        guia=resultado["guia"], tipo=resultado["tipo"], capa=resultado["capa"],
    )


if __name__ == "__main__":
    app.run(host=RRHH_API_HOST, port=5000)
