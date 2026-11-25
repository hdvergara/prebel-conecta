# Flujos: cómo responde cada canal, hoy

Mapa de referencia de **todos** los caminos que puede tomar la pregunta de
un colaborador, con el contrato exacto de cada pieza. Es documentación del
estado actual del código (verificado línea por línea), no un análisis de
decisiones -- eso vive aparte, en los documentos locales de la ronda de
unificación (no versionados todavía).

## 1. Los cinco flujos

| # | Flujo | Entra por | Quién decide la respuesta |
|---|---|---|---|
| 1 | Portal, búsqueda predictiva | Escribir en el buscador | Solo `rank()` de `dist/app.js` -- JS puro, sin red |
| 2 | Portal, "Preguntar al asistente" | Enter sin sugerencia, o clic en el botón | `model/orquestador.py` (vía `POST /reply`) |
| 3 | WhatsApp local (`whatsapp_service.py`) | Webhook del emulador/Meta | `RRHHBot.match()` **directo** -- no pasa por el orquestador, ver nota en §4 |
| 4 | WhatsApp real/emulador por n8n (puertas 01/02) | Webhook de n8n | La cadena **propia de n8n** (su Cerebro), independiente de la de Python |
| 5 | Burbuja de chat del portal (puerta Web de n8n) | Chat Trigger de n8n | Misma cadena que el flujo 4 |

`model/entrenar.py` no es un flujo de respuesta -- calibra umbrales y
embeddings, no contesta preguntas de un colaborador.

## 2. La cadena de Python (flujo 2): predictivo → ML → LLM

Dueña del código: `model/orquestador.py`. Se activa en cada `POST /reply`
que recibe texto no vacío.

```
texto ──► RRHHBot.match(texto) ──► confianza
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
      confianza > 0.95        0.75 ≤ confianza ≤ 0.95   confianza < 0.75
      (o nunca si               (o nunca si pide           (o si pide
       pide "seguir")            "seguir")                  "seguir")
              │                       │                       │
       capa="predictivo"       capa="ml"              conector LLM (MCP)
      (la respuesta del      (la respuesta del              │
       ML, tal cual)          ML, tal cual)         ¿responde? ──no──► capa="ml"
                                                             │          (cae al ML
                                                            sí           ya calculado)
                                                             │
                                                    envuelve con ruta/area/guia
                                                    que el ML ya tenía; si la
                                                    confianza del ML era < 0.75,
                                                    se encola en retroalimentacion.json
                                                    (revisión manual, nunca automática)
                                                             │
                                                      capa="llm", tipo="generado"
```

Los dos umbrales (0.95 y 0.75) y el orden de las capas son datos editables
en `model/arquitectura.json` (cargados por `model/configuracion.py`), no
constantes de código -- ver CONSTITUTION.md R8/R9 para las reglas que esto
debe respetar.

### Contrato de `POST /reply`

```jsonc
// entrada
{ "text": "¿Cuántos días de vacaciones tengo?", "seguir": false }

// salida
{
  "reply": "...",
  "ruta": "vacaciones" | null,
  "area": "Gestión Humana" | null,
  "confianza": 0.92 | null,
  "sentimiento": { "etiqueta": "positivo", "estrellas": 5, "confianza": 0.8 } | null,
  "guia": "..." | null,
  "tipo": "confiado" | "acotar" | "saludo" | "grosero" | "fallback" | "generado" | null,
  "capa": "predictivo" | "ml" | "llm" | null
}
```

- `seguir` es opcional (default `false`): fuerza la escalada al conector
  LLM sin importar el umbral -- pensado para un futuro botón "esto no es
  lo que buscaba" en la UI; **hoy ningún cliente lo manda todavía**
  (`dist/app.js` no lo incluye, el nodo HTTP del Cerebro de n8n tampoco).
- `tipo`/`capa` son aditivos: `dist/app.js` y el Tier 1 de n8n siguen
  leyendo solo los campos que ya conocían (`reply`, `ruta`, `area`,
  `confianza`, `sentimiento`) sin romperse.
- Con texto vacío, todos los campos nuevos (`guia`, `tipo`, `capa`) vienen
  `null`, igual que los que ya existían.

### El conector LLM (capa "llm")

`model/conectores.py` -- intercambiable, vía la variable de entorno
`LLM_CONECTOR`:

| `LLM_CONECTOR` | Conector | Variables relacionadas |
|---|---|---|
| sin definir, o cualquier otro valor | `ConectorNulo` -- nunca responde, el orquestador cae siempre a la respuesta del ML | -- |
| `mcp` | `ConectorMCP` -- se conecta a un servidor MCP y le pide la respuesta | `MCP_SERVIDOR_CMD` (comando a ejecutar) o `MCP_SERVIDOR_URL` (servidor ya corriendo), `MCP_HERRAMIENTA` (nombre de la tool, default `responder_rrhh`) |

Son variables de entorno reales del proceso que corre `rrhh_api.py` (no se
leen de `.env` -- a diferencia de `whatsapp_service.py`, `rrhh_api.py` no
carga `python-dotenv`). Sin ninguna configurada, el comportamiento es
exactamente el de antes de esta cadena: una consulta rápida, sin red
externa, nunca escala.

Hoy no existe un servidor MCP real montado para este proyecto (ni
envolviendo a Ollama ni al RAG de n8n) -- es trabajo de infraestructura
del equipo, fuera de este repo.

## 3. La cadena de n8n (flujos 4 y 5): independiente, sin cambios

El Cerebro de n8n (`n8n/workflows/03-cerebro-ia.json`) tiene su **propia**
cadena de tres niveles, que no pasa por `model/orquestador.py` y no se
tocó en esta ronda:

1. **Predictivo** -- su propio detector de saludo/menú (nodo *Detectar
   saludo*), independiente del de `rrhh_bot.py`.
2. **ML** -- llama a `POST /reply` igual que el flujo 2, pero solo lee
   `confianza` y `reply` de la respuesta; si `confianza ≥ 0,65` la usa
   directo. Como el conector LLM de Python está apagado por defecto
   (`LLM_CONECTOR` sin definir), esta llamada se comporta igual que antes
   de esta ronda -- rápida, sin escalar nunca del lado de Python.
3. **Agentic** -- su propio RAG con Ollama (`embeddinggemma` +
   `gemma4:e2b`) sobre los documentos reales de Prebel.

Ver `n8n/README.md` para el detalle completo de esta cadena (que sigue
siendo la fuente de verdad de cómo responde WhatsApp real).

**Puente opcional entre las dos cadenas:** este mismo Cerebro puede además
servir como *backend* del conector LLM de Python (`LLM_CONECTOR=mcp`
apuntando a un servidor MCP que envuelva este Cerebro) -- en ese caso, el
flujo 2 (portal) podría terminar escalando hasta el RAG real de n8n. Es
opcional y no existe montado hoy; mientras no se configure, las dos
cadenas son completamente independientes.

## 4. Lo que no está unificado todavía (a propósito)

- **Flujo 3 (WhatsApp local) no pasa por el orquestador.**
  `model/whatsapp_service.py` llama a `bot.match(texto)` directo, no a
  `orquestador.responder_pregunta(...)` -- sigue siendo solo capa ML, sin
  el escalado 95/75 ni el conector LLM. No es un descuido de esta ronda:
  es el estado heredado, documentado aquí para que sea visible y se pueda
  decidir a propósito si conviene cambiarlo.
- **`dist/app.js`'s `rank()` sigue siendo JS puro, sin red** (R2,
  `CONSTITUTION.md`) -- nunca puede compartir código con el orquestador ni
  con `RRHHBot`, por diseño.
- **Las dos cadenas de tres niveles (Python y n8n) tienen su propio
  detector de saludo**, cada una independiente -- ver
  `CONSTITUTION.md` R9 y la nota de la sección 3 arriba.

## 5. Dónde vive cada pieza

| Capa | Archivo |
|---|---|
| Predictivo (portal) | `dist/app.js` (`rank()`) |
| ML (semántico + sentimiento) | `model/rrhh_bot.py` |
| Orquestador (95/75, `seguir`, retorno envuelto) | `model/orquestador.py` |
| Spec-Doc editable (umbrales) | `model/arquitectura.json` + `model/configuracion.py` |
| Conector LLM | `model/conectores.py` |
| Cola de retroalimentación | `model/retroalimentacion.py` |
| Contrato HTTP | `model/rrhh_api.py` (`POST /reply`) |
| Canal WhatsApp local | `model/whatsapp_service.py` |
| Cadena propia de n8n | `n8n/workflows/03-cerebro-ia.json` + `n8n/README.md` |
