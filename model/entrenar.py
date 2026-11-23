"""Primer paso tras clonar el repo e instalar dependencias: prepara los dos
modelos preentrenados (los descarga de Hugging Face la primera vez, ~1 GB) y
calibra lo propio del proyecto a partir de los datos actuales.

No entrena los modelos preentrenados -- rrhh_bot.py sigue siendo "sin
entrenamiento propio" (ver CONSTITUTION.md). Esto prepara y ajusta lo que sí
es nuestro:

0. Descarga y deja en caché de Hugging Face los dos modelos preentrenados que
   usa rrhh_bot.py (similitud semántica y sentimiento), para que la primera
   vez que corras la API no tengas que esperar esa descarga ahí.
1. Cachea los embeddings de las frases del FAQ en faq_embeddings.pt, para que
   rrhh_api.py arranque más rápido (no vuelve a codificar las frases si el
   caché sigue vigente para el faq_rrhh.json actual).
2. Recalcula el UMBRAL de similitud a partir de los propios datos: mide qué
   tan parecidas son las frases de un mismo tema entre sí (debería ser alto) y
   qué tan parecidas son frases de temas distintos (debería ser bajo), y
   sugiere un umbral que separe ambos casos. Solo sugiere -- no modifica
   THRESHOLD en rrhh_bot.py; eso lo decide quien revise el resultado.

Con --augmentar además pide a un motor de IA formas adicionales de preguntar
cada tema, para que una persona las revise antes de añadirlas a faq_rrhh.json.
Cualquier desarrollador o ingeniero de IA puede usar el motor que tenga a la
mano -- Ollama (local, sin clave), OpenAI, Claude, Gemini, o un parafraseador
local pequeño que no necesita cuenta ni modelo de chat -- con --motor. Ver
MODEL_TRAINING.md (motores de chat) y MODEL_TUNING.md (el parafraseador
local, por qué se filtran sus sugerencias) para el detalle de cada uno y
cómo configurar su clave. Es opcional: sin el motor elegido disponible, el
resto del script funciona igual.

Uso (PowerShell):
    python model/entrenar.py
    python model/entrenar.py --augmentar
    python model/entrenar.py --augmentar --motor ollama --modelo qwen2.5:7b-instruct
    python model/entrenar.py --augmentar --motor claude --modelo claude-haiku-5-5
    python model/entrenar.py --augmentar --motor openai --modelo gpt-4o-mini
    python model/entrenar.py --augmentar --motor gemini --modelo gemini-2.0-flash
    python model/entrenar.py --augmentar --motor local
"""
import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

from rrhh_bot import MODEL_NAME, SENTIMENT_MODEL, _palabras_clave

BASE = Path(__file__).parent
FAQ_PATH = BASE / "faq_rrhh.json"
EMB_PATH = BASE / "faq_embeddings.pt"


def cargar_faq():
    return json.loads(FAQ_PATH.read_text(encoding="utf-8"))


def _pedir_ollama(prompt, modelo):
    body = json.dumps({"model": modelo, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["response"]


def _pedir_openai(prompt, modelo):
    clave = os.environ.get("OPENAI_API_KEY")
    if not clave:
        raise RuntimeError("falta la variable de entorno OPENAI_API_KEY")
    body = json.dumps({"model": modelo, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {clave}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def _pedir_claude(prompt, modelo):
    clave = os.environ.get("ANTHROPIC_API_KEY")
    if not clave:
        raise RuntimeError("falta la variable de entorno ANTHROPIC_API_KEY")
    body = json.dumps({
        "model": modelo, "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"Content-Type": "application/json", "x-api-key": clave, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["content"][0]["text"]


def _pedir_gemini(prompt, modelo):
    clave = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not clave:
        raise RuntimeError("falta la variable de entorno GEMINI_API_KEY (o GOOGLE_API_KEY)")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={clave}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"]


# "ChatGPT" y "Codex" son nombres de producto sobre esta misma API de OpenAI
# -- no hay una API pública distinta para cada uno. Ver MODEL_TRAINING.md.
MOTORES = {
    "ollama": {"fn": _pedir_ollama, "modelo_por_defecto": "qwen2.5:7b-instruct", "clave_env": None},
    "openai": {"fn": _pedir_openai, "modelo_por_defecto": "gpt-4o-mini", "clave_env": "OPENAI_API_KEY"},
    "claude": {"fn": _pedir_claude, "modelo_por_defecto": "claude-haiku-5-5", "clave_env": "ANTHROPIC_API_KEY"},
    "gemini": {"fn": _pedir_gemini, "modelo_por_defecto": "gemini-2.0-flash", "clave_env": "GEMINI_API_KEY"},
    # Sin cuenta ni modelo de chat -- un modelo pequeño de paráfrasis en
    # español, local. Más barato y rápido que los de arriba, pero de menor
    # calidad: filtra sus propias sugerencias (ver _sugerir_local) y de
    # todas formas sigue pidiendo revisión humana. Detalle y por qué se
    # eligió este modelo en concreto: MODEL_TUNING.md.
    "local": {"fn": None, "modelo_por_defecto": "p-serna/mt5-small-spanish-paraphraser", "clave_env": None},
}

_PARAFRASEADORES_LOCALES = {}  # modelo -> (tokenizer, modelo), cargado una sola vez por ejecución


def _cargar_parafraseador_local(modelo):
    if modelo not in _PARAFRASEADORES_LOCALES:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        print(f"    (cargando parafraseador local {modelo}...)")
        tokenizer = AutoTokenizer.from_pretrained(modelo)
        modelo_cargado = AutoModelForSeq2SeqLM.from_pretrained(modelo)
        _PARAFRASEADORES_LOCALES[modelo] = (tokenizer, modelo_cargado)
    return _PARAFRASEADORES_LOCALES[modelo]


def _sugerir_local(tema, modelo, n=3):
    """Genera paráfrasis de `tema` con un modelo de paráfrasis local (no de
    chat): sin prompt, por beam search directo sobre el texto.

    MODEL_TUNING.md documenta un problema real de este tipo de modelo en
    esta máquina: a veces sustituye una palabra de dominio (p. ej. "nómina")
    por otra más común en sus propios datos de entrenamiento, cambiando el
    sentido de la pregunta sin que se note a simple vista. Por eso cada
    candidata se descarta si no comparte ninguna palabra clave con el tema
    original (reutilizando _palabras_clave de rrhh_bot.py, la misma lógica
    usada ahí para la revisión sintáctica) -- un filtro automático barato,
    no un sustituto de la revisión humana que de todas formas sigue
    haciendo falta antes de tocar faq_rrhh.json."""
    tokenizer, modelo_cargado = _cargar_parafraseador_local(modelo)
    entrada = tokenizer(tema, return_tensors="pt", truncation=True)
    salida = modelo_cargado.generate(
        **entrada, max_length=64, num_beams=5, num_return_sequences=n + 2,
        no_repeat_ngram_size=2, early_stopping=True,
    )
    candidatas = [tokenizer.decode(s, skip_special_tokens=True).strip() for s in salida]

    palabras_tema = _palabras_clave(tema)
    sugeridas, vistas = [], {tema.strip().lower()}
    for candidata in candidatas:
        clave = candidata.lower()
        if clave in vistas:
            continue
        vistas.add(clave)
        if palabras_tema and not (palabras_tema & _palabras_clave(candidata)):
            continue  # probable corrupción de una palabra de dominio -- se descarta sin avisar
        sugeridas.append(candidata)
        if len(sugeridas) == n:
            break
    return sugeridas


def sugerir_frases(tema, motor, modelo, n=3):
    """Pide al motor elegido formas adicionales de preguntar `tema`.
    Devuelve una lista de strings para revisión manual; no escribe nada en
    faq_rrhh.json ni en ningún otro archivo del repositorio."""
    if motor == "local":
        return _sugerir_local(tema, modelo, n)
    prompt = (
        f"Genera {n} formas distintas de preguntar lo siguiente en español de "
        f'Colombia, una por línea, sin numerar ni explicar nada más: "{tema}"'
    )
    texto = MOTORES[motor]["fn"](prompt, modelo)
    return [line.strip() for line in texto.splitlines() if line.strip()]


def calibrar_umbral(model, faq):
    """Separa similitud 'mismo tema' (debería ser alta) de 'temas distintos'
    (debería ser baja) y sugiere un umbral entre el peor de cada grupo."""
    frases, dueno = [], []
    for i, item in enumerate(faq["faq"]):
        for frase in item["preguntas"]:
            frases.append(frase)
            dueno.append(i)
    emb = model.encode(frases, convert_to_tensor=True)
    sim = util.cos_sim(emb, emb)

    mismo_tema, distinto_tema = [], []
    for i in range(len(frases)):
        for j in range(len(frases)):
            if i == j:
                continue
            (mismo_tema if dueno[i] == dueno[j] else distinto_tema).append(float(sim[i][j]))

    peor_mismo = min(mismo_tema)
    peor_distinto = max(distinto_tema)
    return {
        "frases": frases,
        "dueno": dueno,
        "embeddings": emb,
        "peor_similitud_mismo_tema": round(peor_mismo, 3),
        "peor_similitud_distinto_tema": round(peor_distinto, 3),
        "umbral_sugerido": round((peor_mismo + peor_distinto) / 2, 3),
        "hay_superposicion": peor_distinto > peor_mismo,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--augmentar", action="store_true", help="Sugiere frases nuevas con un motor de IA")
    parser.add_argument("--motor", choices=sorted(MOTORES), default="ollama",
                         help="Motor de IA para --augmentar (ver MODEL_TRAINING.md)")
    parser.add_argument("--modelo", default=None,
                         help="Modelo dentro del motor elegido (por defecto, uno razonable por motor)")
    args = parser.parse_args()

    faq = cargar_faq()

    if args.augmentar:
        motor = MOTORES[args.motor]
        modelo = args.modelo or motor["modelo_por_defecto"]
        if motor["clave_env"] and not os.environ.get(motor["clave_env"]):
            print(f"Falta la variable de entorno {motor['clave_env']} para usar --motor {args.motor}.")
            print("Ver MODEL_TRAINING.md para cómo configurarla. Omitiendo --augmentar.\n")
        else:
            print(f"Sugerencias con {args.motor} ({modelo}) -- revisa antes de añadirlas a faq_rrhh.json:\n")
            for item in faq["faq"]:
                tema = item["preguntas"][0]
                print(f"- {tema}")
                try:
                    for sugerida in sugerir_frases(tema, args.motor, modelo):
                        print(f"    {sugerida}")
                except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, OSError, ImportError) as e:
                    print(f"    (no se pudo consultar {args.motor}: {e})")
            print()

    print(f"Cargando {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"Cargando {SENTIMENT_MODEL}...")
    pipeline("sentiment-analysis", model=SENTIMENT_MODEL)  # solo para descargarlo y dejarlo en caché

    resultado = calibrar_umbral(model, faq)
    torch.save({"frases": resultado["frases"], "embeddings": resultado["embeddings"]}, EMB_PATH)

    print(f"\nEmbeddings cacheados en {EMB_PATH} ({len(resultado['frases'])} frases).")
    print(f"Peor similitud dentro del mismo tema:   {resultado['peor_similitud_mismo_tema']}")
    print(f"Peor similitud entre temas distintos:   {resultado['peor_similitud_distinto_tema']}")
    print(f"Umbral sugerido:                        {resultado['umbral_sugerido']}")
    if resultado["hay_superposicion"]:
        print("\nOjo: hay temas que se parecen más entre sí que algunas de sus propias frases.")
        print("Revísalos antes de tocar THRESHOLD en rrhh_bot.py -- un solo número no los va a separar bien.")
    else:
        print(f"\nPuedes ajustar THRESHOLD en rrhh_bot.py a {resultado['umbral_sugerido']} con margen seguro.")


if __name__ == "__main__":
    main()
