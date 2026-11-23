"""Bot de RRHH con modelo preentrenado (sin entrenamiento propio).

Compara la pregunta del empleado con preguntas frecuentes usando embeddings
multilingües y devuelve la respuesta de la más parecida.

Uso (PowerShell):
    python rrhh_bot.py
"""
import json
import re
import unicodedata
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

# Frases de saludo habituales (sin acentos, en minúscula) para dar una
# bienvenida en vez del mensaje de respaldo cuando no hay pregunta real detrás.
SALUDOS = (
    "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches",
    "buen dia", "que mas", "como estas", "como vas", "saludos", "hey",
    "quiubo", "que hubo",
)

# Palabras demasiado comunes en español (y en cómo se suelen formular
# preguntas) para servir como pista de tema en la revisión sintáctica de
# abajo -- sin esto, casi cualquier frase "tocaría" varias entradas del FAQ.
PALABRAS_VACIAS = {
    "para", "como", "cual", "cuales", "cuando", "cuanto", "cuanta", "cuantos",
    "cuantas", "donde", "quiero", "necesito", "tengo", "tiene", "puedo",
    "hacer", "hago", "pedir", "pido", "sobre", "este", "esta", "estos",
    "estas", "algo", "alguna", "algun", "ayuda", "duda", "pregunta", "problema",
    "informacion", "saber", "consultar", "respecto",
    # genéricas de proceso que aparecen en preguntas de varios temas distintos
    # (p. ej. "días" en vacaciones Y en nómina) -- de tomarlas en cuenta, casi
    # cualquier frase "tocaría" un tema por accidente (ver bug de "buenos
    # días" de esta misma sesión, con el matcher de palabras clave de dist/app.js).
    "dias", "dia", "fecha", "fechas",
}
PALABRA_MINIMA = 4  # descarta conectores cortos (de, mi, que ya quedan fuera por no ser palabras)
# Siglas cortas que sí son indicio de tema por su cuenta, pese a no llegar a
# PALABRA_MINIMA (p. ej. "EPS", de solo 3 letras).
SIGLAS_SIGNIFICATIVAS = {"eps"}


def _normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore")
    return sin_acentos.decode("ascii")


def _palabras_clave(frase: str) -> set:
    plano = _normalizar(frase)
    palabras = re.findall(r"[a-z]+", plano)
    return {w for w in palabras if w not in PALABRAS_VACIAS
            and (len(w) >= PALABRA_MINIMA or w in SIGLAS_SIGNIFICATIVAS)}


class RRHHBot:
    """Reutilízala desde Teams, Slack, Telegram o WhatsApp: RRHHBot().reply(texto)."""

    def __init__(self, faq_path: Path = FAQ_PATH):
        data = json.loads(faq_path.read_text(encoding="utf-8"))
        self.fallback = data["fallback"]
        # Opcionales: si el FAQ no los trae (p. ej. un fixture de prueba más
        # viejo), se cae de vuelta al mismo fallback genérico.
        self.saludo = data.get("saludo", self.fallback)
        self.grosero = data.get("grosero", self.fallback)
        self.items = data["faq"]
        self.model = SentenceTransformer(MODEL_NAME)
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=SENTIMENT_MODEL)
        preguntas, self.owner = [], []
        self.palabras_por_item = []
        for i, item in enumerate(self.items):
            palabras = set()
            for q in item["preguntas"]:
                preguntas.append(q)
                self.owner.append(i)
                palabras |= _palabras_clave(q)
            self.palabras_por_item.append(palabras)
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

    def _es_saludo(self, text: str) -> bool:
        plano = _normalizar(text)
        return any(frase in plano for frase in SALUDOS)

    def _candidatos_sintacticos(self, text: str, limite: int = 3) -> list:
        """Revisión sintáctica (palabras clave, no embeddings): entradas del
        FAQ que comparten alguna palabra significativa con el mensaje, aunque
        la frase completa no se pareciera lo suficiente a ninguna pregunta
        registrada. Sirve para distinguir "no tengo idea de qué hablas" de
        "sé el tema, pero no cuál de estas preguntas exactamente" -- y en ese
        segundo caso, pedirle a la persona que lo precise en vez de adivinar."""
        palabras_texto = _palabras_clave(text)
        if not palabras_texto:
            return []
        puntajes = []
        for i, palabras_item in enumerate(self.palabras_por_item):
            coincidencias = len(palabras_texto & palabras_item)
            if coincidencias:
                puntajes.append((coincidencias, i))
        puntajes.sort(key=lambda t: -t[0])
        return [self.items[i] for _, i in puntajes[:limite]]

    def _respuesta_para_acotar(self, candidatos: list) -> str:
        opciones = "; ".join(item["preguntas"][0] for item in candidatos)
        return (f"Creo que tu pregunta es sobre esto: {opciones}. "
                "Cuéntame cuál te interesa (o escribe tu pregunta lo más parecido posible a una de esas) "
                "para darte la respuesta exacta.")

    def match(self, text: str) -> dict:
        """Intención detectada: respuesta más la ruta/área de la app ligadas a esa pregunta,
        la confianza de la coincidencia semántica y el sentimiento del mensaje.

        Sin una coincidencia segura (confianza < THRESHOLD), en vez de caer
        siempre al mismo mensaje de respaldo frío, se prioriza así: (1) tono
        negativo, que se reconoce antes que nada; (2) si el tono no es
        negativo pero el mensaje comparte palabras clave con uno o más temas
        del FAQ (revisión sintáctica, no semántica), se le pide a la persona
        que acote su pregunta a cuál de esos temas, en vez de adivinar o
        devolver el genérico; (3) un saludo sin pregunta real detrás recibe
        una bienvenida; (4) cualquier otro caso usa el respaldo genérico."""
        q = self.model.encode(text, convert_to_tensor=True)
        scores = util.cos_sim(q, self.emb)[0]
        best = int(scores.argmax())
        confianza = round(float(scores[best]), 2)
        sentimiento = self.sentiment(text)
        if confianza < THRESHOLD:
            candidatos = self._candidatos_sintacticos(text)
            if sentimiento["etiqueta"] == "negativo":
                respuesta = self.grosero
            elif candidatos:
                respuesta = self._respuesta_para_acotar(candidatos)
            elif self._es_saludo(text):
                respuesta = self.saludo
            else:
                respuesta = self.fallback
            return {"respuesta": respuesta, "ruta": None, "area": None, "confianza": confianza, "sentimiento": sentimiento, "guia": None}
        item = self.items[self.owner[best]]
        # "guia" es el paso accionable por su cuenta, sin la frase que remite
        # a "revisa tu perfil" -- la usan canales que ya pueden dar el dato
        # real (ver model/whatsapp_service.py) para no repetir ambas cosas.
        return {"respuesta": item["respuesta"], "ruta": item.get("ruta"), "area": item.get("area"), "confianza": confianza, "sentimiento": sentimiento, "guia": item.get("guia")}

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
