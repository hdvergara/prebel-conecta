"""RAG de reuso sobre la cola de retroalimentación (ver CONSTITUTION.md R9
y model/retroalimentacion.py): antes de que model/orquestador.py escale de
verdad al conector LLM, busca aquí si una pregunta parecida ya fue resuelta
antes por ese mismo conector -- si la hay, se reusa esa respuesta sin pagar
el costo de llamarlo otra vez.

No carga su propio modelo de embeddings: recibe el `SentenceTransformer`
que ya cargó RRHHBot, por inyección -- evita duplicar los ~400 MB del
modelo, y evita que este módulo tenga que importar rrhh_bot (R9: cada capa
solo conoce lo que necesita, no la capa ML completa).

No cachea embeddings entre llamadas: la cola de retroalimentación es de
tamaño de demo (preguntas que las capas anteriores no sabían, revisadas
manualmente de vez en cuando, ver model/entrenar.py
--revisar-retroalimentacion), no un corpus grande -- recalcular en cada
llamada es la opción simple a propósito, no una limitación a resolver
todavía.
"""
from configuracion import UMBRAL_RETROALIMENTACION
from retroalimentacion import listar_pendientes


def buscar_similar(modelo, texto: str) -> dict | None:
    """None si la cola está vacía, si nada alcanza UMBRAL_RETROALIMENTACION,
    o si el cálculo falla por cualquier motivo -- nunca lanza, misma caída
    controlada que el resto de la cadena (R8): sin una coincidencia
    clara, el orquestador debe seguir su camino normal (escalar al
    conector), no fallar."""
    pendientes = listar_pendientes()
    if not pendientes:
        return None
    try:
        from sentence_transformers import util

        validas = [
            p for p in pendientes
            if isinstance(p, dict) and "pregunta" in p and "respuesta" in p
        ]
        if not validas:
            return None

        preguntas = [p["pregunta"] for p in validas]
        embeddings = modelo.encode(preguntas, convert_to_tensor=True)
        consulta = modelo.encode(texto, convert_to_tensor=True)
        puntajes = util.cos_sim(consulta, embeddings)[0]
        mejor = int(puntajes.argmax())
        if float(puntajes[mejor]) < UMBRAL_RETROALIMENTACION:
            return None
        return {"respuesta": validas[mejor]["respuesta"], "contexto": validas[mejor].get("contexto", {})}
    except Exception:
        return None
