# Entrenamiento y calibración del modelo

Este documento es para quien vaya a tocar `model/entrenar.py` o a reentrenar/
recalibrar el bot: qué modelos usa hoy, con qué configuración, cómo ponerlo en
marcha desde un clon nuevo del repositorio, y cómo correr la calibración y
(opcionalmente) la generación de frases nuevas con cualquier motor de IA que
tengas a mano -- no hace falta tener Claude Code ni ningún motor en particular
instalado para esto. Las reglas de fondo (qué no se puede hacer, qué significa
"verde") están en `CONSTITUTION.md`; esto es el detalle técnico de cómo se
prepara y se calibra el modelo.

## Primera vez (clon nuevo, sin nada descargado todavía)

Esto asume que no has corrido nada de `prebel-conecta` antes -- ni la API, ni
los tests, ni `entrenar.py`. Desde `prebel-conecta/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

python model/entrenar.py
```

Ese último comando -- `python model/entrenar.py`, sin ningún flag -- **es el
script/prompt inicial que genera el modelo**: la primera vez que lo corres,
descarga de Hugging Face los dos modelos preentrenados que usa el bot
(`paraphrase-multilingual-MiniLM-L12-v2` para similitud y
`nlptown/bert-base-multilingual-uncased-sentiment` para sentimiento, ~1 GB en
total) y los deja en caché en tu máquina (la ruta por defecto de Hugging Face,
normalmente `~/.cache/huggingface`). Dependiendo de tu conexión puede tardar
varios minutos; es normal, y solo pasa una vez. Después de eso, calcula y
cachea los embeddings del FAQ (`model/faq_embeddings.pt`) y calibra el umbral
-- ver el detalle de cada paso más abajo.

No hace falta correr nada más antes de poder usar la API o los trámites:
`model/rrhh_api.py` reutiliza la misma caché de Hugging Face que acabas de
llenar, así que su primer arranque ya no tiene que descargar nada.

```powershell
python model/rrhh_api.py   # http://127.0.0.1:5000, ya sin descargas pendientes
```

Si prefieres no correr `entrenar.py` primero, también funciona: la API
descarga los modelos ella misma en su propio primer arranque. La diferencia
es solo cuándo pagas esa espera -- `entrenar.py` la adelanta y de paso deja
calculado el umbral y el caché de embeddings.

## Configuración actual

| Pieza | Valor | Dónde |
|---|---|---|
| Modelo de similitud semántica | `paraphrase-multilingual-MiniLM-L12-v2` (Sentence-Transformers, preentrenado) | `model/rrhh_bot.py:MODEL_NAME` |
| Modelo de sentimiento | `nlptown/bert-base-multilingual-uncased-sentiment` (preentrenado, salida de 1 a 5 estrellas) | `model/rrhh_bot.py:SENTIMENT_MODEL` |
| Umbral de similitud (THRESHOLD) | `0.65` | `model/rrhh_bot.py:THRESHOLD` |
| Caché de embeddings | `model/faq_embeddings.pt` (generado por `entrenar.py`, no versionado) | `model/rrhh_bot.py:EMB_CACHE` |
| Datos de entrada | `model/faq_rrhh.json` (45 frases en 15 temas, al momento de escribir esto) | -- |

Ninguno de los dos modelos preentrenados se entrena ni se ajusta (*fine-tune*)
en este proyecto -- se usan tal cual los publica Hugging Face. Lo único
"entrenado" localmente es el **umbral**, y eso se hace por calibración
estadística sobre los datos propios, no por descenso de gradiente.

`THRESHOLD` ya pasó por una ronda real de calibración: originalmente estaba en
`0.55`; subió a `0.65` porque preguntas fuera del FAQ (p. ej. "no me han pagado
horas extras") se parecían ~0.60 a la entrada de nómina y el bot respondía con
eso por error. El comentario junto a la constante en `rrhh_bot.py` documenta
este caso puntual.

## Qué hace `entrenar.py`

```powershell
python model/entrenar.py
```

0. Carga los dos modelos preentrenados reales (no un sustituto -- a diferencia
   de los unit tests, que sí los simulan). Si es la primera vez en esta
   máquina, aquí es donde se descargan de Hugging Face.
1. Carga `model/faq_rrhh.json` y calcula los embeddings de las 45 frases con
   el modelo de similitud.
2. Guarda esos embeddings en
   `model/faq_embeddings.pt`. `rrhh_bot.py` los usa automáticamente la
   próxima vez que arranque (si las frases y la dimensión del embedding
   siguen coincidiendo) en vez de volver a calcularlos -- arranque más rápido.
   Si el caché no existe o quedó desactualizado, no pasa nada: se recalculan
   igual que siempre. Nunca es una dependencia dura.
3. Calibra el umbral: mide la similitud entre todas las frases, separa los
   pares que son "del mismo tema" (debería salir alta) de los que son "de
   temas distintos" (debería salir baja), y a partir de ahí reporta:
   - la peor similitud dentro de un mismo tema,
   - la peor (osea, la más alta) similitud entre temas distintos,
   - un umbral sugerido a medio camino entre ambas.

   Esto es una **sugerencia impresa en consola**, no un cambio automático.
   Decidir si mover `THRESHOLD` en `rrhh_bot.py` es de quien revise el
   resultado -- sobre todo si el script avisa que hay temas que se
   superponen (dos temas que se parecen más entre sí que algunas de sus
   propias frases; un solo número no los va a separar bien, y forzarlo puede
   hacer que el bot deje de reconocer paráfrasis legítimas en otro tema).

## Generar frases nuevas con un motor de IA (`--augmentar`)

```powershell
python model/entrenar.py --augmentar --motor <ollama|openai|claude|gemini> [--modelo <nombre>]
```

Pide al motor elegido 3 formas adicionales de preguntar cada tema del FAQ, y
las **imprime para revisión humana** -- el script nunca escribe en
`faq_rrhh.json` por su cuenta. Cualquier desarrollador o ingeniero de IA
puede correr esto con el motor que ya tenga disponible; ninguno es
obligatorio y el resto del script (caché + calibración) funciona igual sin
`--augmentar`.

| `--motor` | Qué es | Clave necesaria | Dónde se consigue | `--modelo` por defecto |
|---|---|---|---|---|
| `ollama` | Modelo local, sin clave, sin costo por uso | Ninguna | `ollama pull <modelo>` primero | `qwen2.5:7b-instruct` |
| `openai` | API de OpenAI | `OPENAI_API_KEY` | platform.openai.com | `gpt-4o-mini` |
| `claude` | API de Anthropic (Claude) | `ANTHROPIC_API_KEY` | console.anthropic.com | `claude-haiku-5-5` |
| `gemini` | API de Google (Gemini) | `GEMINI_API_KEY` (o `GOOGLE_API_KEY`) | aistudio.google.com | `gemini-2.0-flash` |

**"ChatGPT" y "Codex" no son motores aparte**: ambos son nombres de producto
sobre la misma API de OpenAI (`--motor openai`); no existe una API pública
distinta para cada uno. Lo mismo aplica si alguien tiene acceso a Claude solo
por la app o por Claude Code en vez de por la API -- para este script hace
falta específicamente la clave de API (`ANTHROPIC_API_KEY`), que es un
producto distinto a una suscripción de chat.

Configurar la clave (ejemplo con OpenAI; igual para los demás, cambiando el
nombre de la variable):

```powershell
$env:OPENAI_API_KEY = "sk-..."
python model/entrenar.py --augmentar --motor openai
```

Si la variable de entorno correspondiente no está configurada, el script lo
dice claramente y sigue con la calibración sin generar frases -- no falla.

### Por qué Ollama usa `qwen2.5:7b-instruct` y no `qwen3`

Se probaron ambos en esta máquina (i5 de 12.ª gen, 6 GB de VRAM). `qwen3:4b`
es un modelo "razonador": antes de responder genera un bloque interno de
razonamiento de ~2000 tokens que ni `"think": false` en la API ni la directiva
`/no_think` en el prompt lograron suprimir, lo que se traducía en 190-267
segundos por frase -- impracticable para generar sugerencias de 15+ temas.
`qwen2.5:7b-instruct` (de la misma familia, pero sin ese modo de
razonamiento) responde en unos 2-8 segundos con calidad de español
comparable o mejor. Si vas a usar Ollama con otro modelo, confirma primero
que no sea una variante "razonadora" antes de asumir que será rápido.

## Verificar que nada se rompió

Después de calibrar o de tocar `faq_rrhh.json`, corre la suite completa (ver
`README.md` → Tests, reglas completas en `CONSTITUTION.md` → Harness):

```powershell
pytest tests -v
node --test tests/js
cd e2e && npx playwright test
```

Los unit tests de Python **no** cargan los modelos reales (usan sustitutos
deterministas, ver `tests/fakes.py`), así que no se ven afectados por correr
`entrenar.py` ni por el contenido de `model/faq_embeddings.pt`.

## Variancia de frases: ¿aportaría un modelo de paráfrasis local?

Exploración puntual (no implementada) de si un modelo de paráfrasis en
español pequeño y local, además de los 4 motores de chat de arriba, serviría
para `--augmentar`. Resultado: dos candidatos probados, con problemas de
calidad reales (uno corrompe vocabulario de dominio, el otro cambia la
persona gramatical de la pregunta) -- ver el detalle completo, los
resultados exactos y la recomendación en [`MODEL_TUNING.md`](MODEL_TUNING.md).
