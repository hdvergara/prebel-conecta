"""Orquestador de la cadena de tres capas (ver CONSTITUTION.md R8/R9):
Python, no n8n, decide aquí cuándo una respuesta ya es suficientemente
confiable (capa "predictivo"), cuándo usar la respuesta semántica local tal
cual (capa "ml"), y cuándo escalar al conector LLM (capa "llm") -- la única
capa que puede hablarle a model/conectores.py.

Los dos umbrales (model/configuracion.py) se leen como dato editable, no
como constantes de código. pedir_continuar es el futuro botón "esto no es
lo que buscaba" del lado de quien llama (todavía no conectado desde
dist/app.js ni n8n en este branch, pero el contrato ya lo admite): salta
directo al conector LLM sin importar el umbral.
"""
from configuracion import UMBRAL_LLM, UMBRAL_PREDICTIVO
from conectores import ConectorLLM, crear_conector
from retroalimentacion import registrar


class Orquestador:
    def __init__(self, bot, conector: ConectorLLM | None = None):
        self.bot = bot
        self.conector = conector if conector is not None else crear_conector()

    def responder_pregunta(self, texto: str, pedir_continuar: bool = False) -> dict:
        resultado = self.bot.match(texto)
        confianza = resultado["confianza"]

        if not pedir_continuar and confianza > UMBRAL_PREDICTIVO:
            return {**resultado, "capa": "predictivo"}
        if not pedir_continuar and confianza >= UMBRAL_LLM:
            return {**resultado, "capa": "ml"}

        contexto = {"ruta": resultado["ruta"], "area": resultado["area"]}
        respuesta_llm = self.conector.responder(texto, contexto)
        if respuesta_llm is None:
            # Caída controlada: sin conector disponible o sin respuesta, se
            # usa lo que la capa ML ya tenía en vez de dejar al usuario sin nada.
            return {**resultado, "capa": "ml"}

        if confianza < UMBRAL_LLM:
            # El LLM respondió algo que las capas anteriores no tenían con
            # confianza -- se guarda como candidata para que el equipo la
            # revise (ver model/retroalimentacion.py), nunca se auto-promueve.
            # Si falla (disco lleno, permisos, el lock colgado -- TimeoutError,
            # no solo OSError...), nunca debe tumbar una respuesta que ya está
            # lista para el usuario: esta cola es una comodidad, no un
            # requisito para responder.
            try:
                registrar(texto, respuesta_llm, contexto)
            except Exception:
                pass

        # "Retorno en forma inversa": la respuesta del LLM se envuelve con
        # ruta/area/guia que el ML ya tenía calculados, en vez de perderlos.
        # tipo="generado" (no el tipo interno del ML) porque el texto ya no
        # es una entrada elegida del FAQ ni uno de los mensajes canónicos
        # (grosero/saludo/fallback): lo escribió el conector LLM.
        return {
            "respuesta": respuesta_llm,
            "ruta": resultado["ruta"],
            "area": resultado["area"],
            "confianza": confianza,
            "sentimiento": resultado["sentimiento"],
            "guia": resultado["guia"],
            "tipo": "generado",
            "capa": "llm",
        }
