#!/usr/bin/env python3
"""Exporta los tres flujos Prebel desde n8n a n8n/workflows/.

Uso (desde la raíz del proyecto, en el servidor):
    python3 -I scripts/exportar_flujos.py

Qué escribe:
- 01-puerta-emulador.json y 02-puerta-evolution.json, tal cual (no tienen datos personales).
- 03-cerebro-ia.real.json: copia exacta del cerebro, con nombres y teléfono reales.
  Está en .gitignore: NUNCA subirla.
- 03-cerebro-ia.json: el mismo cerebro con los datos personales cambiados por marcadores
  ([Nombre], [teléfono de Gestión Humana]). Esta sí se puede subir.

La lista de textos reales a reemplazar vive en data/reemplazos.json (fuera de git), para que
los nombres reales no queden escritos en este script. Si después de reemplazar queda algún
número largo o correo, el script se detiene y no escribe la versión para git.

Lee la URL y la API key de n8n de ~/.claude.json (configuración del MCP); no las imprime.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "n8n" / "workflows"
FLUJOS = {
    "qqAw2jiKBTNB0Om8": "01-puerta-emulador",
    "AebrMdUeDZIrEYj4": "02-puerta-evolution",
    "FMh0nT4mwTi0x72z": "03-cerebro-ia",
}
CON_DATOS_REALES = {"03-cerebro-ia"}
# números de 7+ cifras que no sean parte de un identificador interno (UUID), y correos
SOSPECHOSO = re.compile(r"(?<![0-9a-fA-F-])\d{7,}(?![0-9a-fA-F-])|[\w.+-]+@[\w-]+\.[\w.]+")


def leer_flujo(env, wid):
    req = urllib.request.Request(f"{env['N8N_API_URL'].rstrip('/')}/api/v1/workflows/{wid}",
                                 headers={"X-N8N-API-KEY": env["N8N_API_KEY"]})
    with urllib.request.urlopen(req, timeout=30) as r:
        w = json.loads(r.read())
    return {k: w[k] for k in ("name", "nodes", "connections", "settings") if k in w}


def main():
    env = json.loads((Path.home() / ".claude.json").read_text())["projects"]["/home/ubuntu"]["mcpServers"]["n8n-mcp"]["env"]
    reemplazos = json.loads((RAIZ / "data" / "reemplazos.json").read_text(encoding="utf-8"))["reemplazos"]
    for wid, nombre in FLUJOS.items():
        texto = json.dumps(leer_flujo(env, wid), ensure_ascii=False, indent=2) + "\n"
        if nombre in CON_DATOS_REALES:
            (SALIDA / f"{nombre}.real.json").write_text(texto, encoding="utf-8")
            for real, marcador in reemplazos.items():
                texto = texto.replace(real, marcador)
        restos = SOSPECHOSO.findall(texto)
        if restos:
            sys.exit(f"{nombre}: quedan {len(restos)} números largos o correos; agrégalos a data/reemplazos.json. No se escribió.")
        (SALIDA / f"{nombre}.json").write_text(texto, encoding="utf-8")
        print(f"{nombre}.json listo", file=sys.stderr)


if __name__ == "__main__":
    main()
