#!/usr/bin/env python3
"""Calcula los embeddings de data/kb.json con Ollama y carga las fichas en la Data Table de n8n.

Uso (desde la raíz del proyecto, en el servidor):
    python3 -I scripts/cargar_kb.py <ID_DATA_TABLE>
Borra las filas existentes de la tabla y las vuelve a cargar (la tabla es solo una copia de kb.json).
Lee la URL y la API key de n8n de las variables N8N_API_URL y N8N_API_KEY; si no existen, de
~/.claude.json (configuración del MCP en el servidor CORE-LAB). No las imprime.
Ollama: variable OLLAMA_URL (por ejemplo http://localhost:11434); si no existe, busca el contenedor
de Ollama del servidor CORE-LAB.
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
OLLAMA_CONTENEDOR = "ollama-api-wpcngxcjd6adcnm4x8aa1koi"
MODELO = "embeddinggemma"


def http(metodo, url, cuerpo=None, cabeceras=None, timeout=120):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, datos, {"Content-Type": "application/json", **(cabeceras or {})}, method=metodo)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        texto = r.read().decode()
        return json.loads(texto) if texto else {}


def texto_para_embedding(f):
    # formato recomendado para documentos en embeddinggemma
    return f"title: {f['documento']} › {f['seccion']} | text: {f['texto']}"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    tabla = sys.argv[1]
    ollama = os.environ.get("OLLAMA_URL") or "http://" + subprocess.check_output(
        ["docker", "inspect", OLLAMA_CONTENEDOR, "--format",
         "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}"]).decode().split()[0] + ":11434"
    kb = json.loads((RAIZ / "data" / "kb.json").read_text(encoding="utf-8"))
    entradas = [texto_para_embedding(f) for f in kb]
    vectores = []
    for i in range(0, len(entradas), 16):
        r = http("POST", f"{ollama.rstrip('/')}/api/embed", {"model": MODELO, "input": entradas[i:i + 16], "keep_alive": "30m"}, timeout=600)
        vectores.extend(r["embeddings"])
    for f, v in zip(kb, vectores):
        f["embedding"] = [round(x, 5) for x in v]
    (RAIZ / "data" / "kb.json").write_text(json.dumps(kb, ensure_ascii=False), encoding="utf-8")
    print(f"{len(kb)} embeddings de {len(vectores[0])} dimensiones", file=sys.stderr)

    if os.environ.get("N8N_API_URL") and os.environ.get("N8N_API_KEY"):
        env = {k: os.environ[k] for k in ("N8N_API_URL", "N8N_API_KEY")}
    else:
        cfg = json.loads((Path.home() / ".claude.json").read_text())
        env = cfg["projects"]["/home/ubuntu"]["mcpServers"]["n8n-mcp"]["env"]
    base = env["N8N_API_URL"].rstrip("/") + f"/api/v1/data-tables/{tabla}/rows"
    cab = {"X-N8N-API-KEY": env["N8N_API_KEY"]}
    # vaciar la tabla
    while True:
        filas = http("GET", base + "?limit=250", cabeceras=cab).get("data", [])
        if not filas:
            break
        filtro = json.dumps({"type": "or", "filters": [{"columnName": "id", "condition": "eq", "value": f["id"]} for f in filas]})
        http("DELETE", base + "/delete?filter=" + urllib.parse.quote(filtro), cabeceras=cab)
    filas = [{"ficha_id": f["id"], "documento": f["documento"], "seccion": f["seccion"],
              "texto": f["texto"], "embedding": json.dumps(f["embedding"])} for f in kb]
    for i in range(0, len(filas), 25):
        http("POST", base, {"data": filas[i:i + 25], "returnType": "count"}, cab)
    print(f"{len(filas)} fichas cargadas en la tabla {tabla}", file=sys.stderr)


if __name__ == "__main__":
    import urllib.parse  # noqa: E402
    main()
