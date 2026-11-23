"""Bot de RRHH con modelo preentrenado (sin entrenamiento propio).

Compara la pregunta del empleado con preguntas frecuentes usando embeddings
multilingües y devuelve la respuesta de la más parecida.

Uso (PowerShell):
    python rrhh_bot.py
"""
import json
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

BASE = Path(__file__).parent
FAQ_PATH = BASE / "faq_rrhh.json"
EMB_CACHE = BASE / "faq_embeddings.pt"  # generado por entrenar.py; opcional
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # preentrenado, soporta español
SENTIMENT_MODEL = "nlptown/bert-base-multilingual-uncased-sentiment"  # preentrenado, salida de 1 a 5 estrellas
# 0.65, no 0.55: una pregunta fuera del FAQ (p. ej. "horas extras") puede
# parecerse ~0.60 a nómina y antes se respondía con esa entrada.
THRESHOLD = 0.65  # similitud mínima; por debajo se escala a una persona de RRHH


class RRHHBot:
    """Reutilízala desde Teams, Slack, Telegram o WhatsApp: RRHHBot().reply(texto)."""

    def __init__(self, faq_path: Path = FAQ_PATH):
        data = json.loads(faq_path.read_text(encoding="utf-8"))
        self.fallback = data["fallback"]
        self.items = data["faq"]
        self.model = SentenceTransformer(MODEL_NAME)
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=SENTIMENT_MODEL)
        preguntas, self.owner = [], []
        for i, item in enumerate(self.items):
            for q in item["preguntas"]:
                preguntas.append(q)
                self.owner.append(i)
        self.emb = self._cargar_cache(preguntas)
        if self.emb is None:
            self.emb = self.model.encode(preguntas, convert_to_tensor=True)

    def _cargar_cache(self, preguntas):
        """Usa los embeddings de entrenar.py si existen, siguen vigentes para
        las frases actuales de faq_rrhh.json, Y coinciden en dimensión con lo
        que el modelo actual produce (si alguien cambia MODEL_NAME, o en
        pruebas donde el modelo está simulado, un caché con otra dimensión no
        sirve). Si cualquiera de los dos no se cumple, devuelve None y
        __init__ calcula los embeddings de nuevo -- el caché es solo una
        optimización, nunca una dependencia."""
        if not EMB_CACHE.exists():
            return None
        try:
            cache = torch.load(EMB_CACHE, weights_only=False)
        except Exception:
            return None
        if cache.get("frases") != preguntas:
            return None
        embeddings = cache["embeddings"]
        if embeddings.shape[-1] != self.model.encode(preguntas[0]).shape[-1]:
            return None
        return embeddings

    def sentiment(self, text: str) -> dict:
        """Sentimiento del mensaje, a partir de las 1-5 estrellas del modelo preentrenado."""
        result = self.sentiment_pipeline(text[:512])[0]
        estrellas = int(result["label"][0])
        etiqueta = "negativo" if estrellas <= 2 else "positivo" if estrellas >= 4 else "neutral"
        return {"etiqueta": etiqueta, "estrellas": estrellas, "confianza": round(float(result["score"]), 2)}

    def match(self, text: str) -> dict:
        """Intención detectada: respuesta más la ruta/área de la app ligadas a esa pregunta,
        la confianza de la coincidencia semántica y el sentimiento del mensaje."""
        q = self.model.encode(text, convert_to_tensor=True)
        scores = util.cos_sim(q, self.emb)[0]
        best = int(scores.argmax())
        confianza = round(float(scores[best]), 2)
        sentimiento = self.sentiment(text)
        if confianza < THRESHOLD:
            return {"respuesta": self.fallback, "ruta": None, "area": None, "confianza": confianza, "sentimiento": sentimiento}
        item = self.items[self.owner[best]]
        return {"respuesta": item["respuesta"], "ruta": item.get("ruta"), "area": item.get("area"), "confianza": confianza, "sentimiento": sentimiento}

    def reply(self, text: str) -> str:
        return self.match(text)["respuesta"]


if __name__ == "__main__":
    bot = RRHHBot()
    print("Asistente de RRHH listo. Escribe 'salir' para terminar.")
    while True:
        text = input("Tú: ").strip()
        if text.lower() in {"salir", "exit", "quit"}:
            break
        if text:
            print(f"RRHH: {bot.reply(text)}")
