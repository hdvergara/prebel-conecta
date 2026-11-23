# Ajuste de variancia del FAQ: modelo de paráfrasis local

Este documento registra una exploración de si vale la pena **expandir la
variancia de frases** del FAQ (más formas de preguntar cada tema) usando un
modelo de paráfrasis **pequeño y local**, en vez de depender siempre de
Ollama o de una API paga (`entrenar.py --augmentar`, ver
`MODEL_TRAINING.md`). La motivación de fondo es la misma de siempre en este
proyecto: capas baratas primero, motor pago solo cuando de verdad hace falta
-- aquí, específicamente, evitar que generar más variancia de entrenamiento
dependa de un modelo de chat completo (Ollama) o de una cuenta paga, si un
modelo chico y gratuito alcanza.

**Estado: implementado como `--motor local`** (ver la última sección). La
exploración de abajo -- probar a ciegas, comparar candidatos, aceptar que
ninguno es confiable sin filtro -- es la razón de las decisiones de diseño
de esa implementación, no solo historia.

## Candidatos considerados

Modelos de Hugging Face, entrenados específicamente para parafrasear en
español (no modelos de chat de propósito general):

| Modelo | Base | Datos de entrenamiento | Licencia |
|---|---|---|---|
| [`p-serna/mt5-small-spanish-paraphraser`](https://huggingface.co/pserna/mt5-small-spanish-paraphraser) | `google/mt5-small` | PAWS-X (español) + preguntas duplicadas de Quora traducidas (en→es, Helsinki-NLP/opus-mt-en-es) | Apache-2.0 |
| [`milyiyo/paraphraser-spanish-t5-base`](https://huggingface.co/milyiyo/paraphraser-spanish-t5-base) | T5 español nativo (flax-community) | PAWS-X + TaPaCo | -- |
| [`milyiyo/paraphraser-spanish-t5-small`](https://huggingface.co/milyiyo/paraphraser-spanish-t5-small) | T5 español nativo, versión small | PAWS-X + TaPaCo | MIT |
| [`mrm8488/bert2bert_shared-spanish-finetuned-paus-x-paraphrasing`](https://huggingface.co/mrm8488/bert2bert_shared-spanish-finetuned-paus-x-paraphrasing) | BERT2BERT (encoder-decoder compartido) | PAWS-X (español) | -- |

Advertencia que ya traían las propias fichas de modelo: son de 2022-2023,
con pocas descargas (el de `p-serna`, por ejemplo, marcaba 19 descargas en
el último mes) y fichas de modelo delgadas -- ninguna documenta el formato
de entrada esperado (¿hace falta un prefijo tipo `"paraphrase: "`?) ni
parámetros de generación recomendados. Se probó a ciegas, con una receta de
generación razonable (`num_beams=5`, `num_return_sequences=3`,
`no_repeat_ngram_size=2`), igual que se calibró `qwen2.5:7b-instruct` contra
`qwen3` en `MODEL_TRAINING.md` -- probar en esta misma máquina en vez de
asumir a partir de la ficha.

De los cuatro, solo se probaron los dos primeros (el de `p-serna` por ser el
más alineado al caso de uso -- preguntas duplicadas, no solo oraciones
parecidas en general -- y el `t5-base` de `milyiyo` por reportar la mejor
pérdida de validación de su familia). El `t5-small` de `milyiyo` y el
`bert2bert` de `mrm8488` quedan sin probar.

## Método

Contra 4-5 preguntas reales de `model/faq_rrhh.json`, cargando cada modelo
con `transformers` (`AutoTokenizer` + `AutoModelForSeq2SeqLM`, ya
dependencias del proyecto; solo hizo falta añadir `sentencepiece` para el
tokenizer de mT5) y generando 3 variantes por pregunta.

## Resultados

**`p-serna/mt5-small-spanish-paraphraser`** (sin prefijo):

```
¿Cómo solicito vacaciones?
  ¿Cómo puedo solicitar vacaciones?
  ¿Cuál es la mejor manera de solicitar vacaciones?
  ¿Cómo puedo solicitar una vacaciones?          <- concordancia rota ("una vacaciones")

¿Cómo pido un certificado laboral?
  ¿Cómo puedo pedir un certificado laboral?
  ¿Cómo puedo obtener un certificado laboral?
  ¿Cómo puedo tomar un certificado laboral?      <- verbo que no encaja

¿Cuándo pagan la nómina?
  ¿Cuándo pagar la opinión?                      <- "nómina" reemplazada por "opinión"
  ¿Cuándo debería pagar la opinión?              <- igual
  ¿Cuándo puedo pagar la opinión?                <- igual

¿Cómo retiro mis cesantías?
  ¿Cómo puedo retirar mis cesantías?
  ¿Cómo retiro mis cesantías?                    (idéntica a la original)
  ¿Cómo puedo retirar mi cesantías?              <- concordancia rota ("mi cesantías")
```

Con el prefijo `"paraphrase: "` el caso de "nómina" mejora parcialmente
(`"¿Cuándo pagar la nomina?"`, sin tilde pero correcta, aparece 2 de 3
veces), pero no desaparece del todo -- sigue saliendo `"opinión"` en una de
las tres variantes. El prefijo no tiene base documentada; se probó porque es
la convención común en modelos T5 multi-tarea, pero este no parece
necesitarlo ni responder de forma consistente a él.

**`milyiyo/paraphraser-spanish-t5-base`** (misma receta, sin prefijo):

```
¿Cómo solicito vacaciones?
  Cómo solicito vacaciones?
  Cómo solicita vacaciones?    <- cambia la persona gramatical: ya no es "yo", es "él/ella/usted"
  Cómo solicitas vacaciones?   <- cambia a "tú"

¿Cómo pido un certificado laboral?
  Cómo pido un certificado laboral?
  Cómo pide un certificado laboral?
  Cómo pida un certificado laboral?

¿Cuándo pagan la nómina?
  Cuándo pagan la nómina?
  Cuándo viene la nómina?
  Cuándo llegarás la nómina?   <- conjugación que no concuerda con el sujeto

¿Cómo retiro mis cesantías?
  Cómo retiro mis cesantas?    <- "cesantías" corrompida a "cesantas"
  Cómo retira mis cesantas?
  Cómo retirán mis cesantas?
```

(También se come la `¿` de apertura en todas las salidas -- eso sí sería
trivial de corregir con posprocesamiento, no es el problema de fondo.)

## Veredicto

Ninguno de los dos es confiable para automatizar sin revisión -- lo cual no
rompe nada, porque `entrenar.py --augmentar` **ya** está diseñado para que
toda sugerencia pase por revisión humana antes de tocar `faq_rrhh.json` (ver
`MODEL_TRAINING.md`); esto solo confirma que esa disciplina sigue siendo
obligatoria, no opcional, con estos modelos.

Entre los dos:

- **`p-serna/mt5-small-spanish-paraphraser` es claramente mejor** -- sus
  errores son de vocabulario puntual (confunde "nómina" con una palabra más
  común en sus datos de entrenamiento), pero preserva el sentido de la
  pregunta.
- **`milyiyo/paraphraser-spanish-t5-base` no se recomienda** -- cambia la
  persona gramatical (de "yo solicito" a "tú solicitas" o "él solicita"),
  lo que no es una paráfrasis: es una pregunta distinta, hecha por o sobre
  otra persona. Para preguntas de autoservicio ("mis vacaciones", "mi
  certificado") esto es un defecto serio, no cosmético.

Problema aparte de los errores puntuales: **poca diversidad real**. La
mayoría de las variantes de `p-serna` son la misma oración envuelta en
"¿Cómo puedo...?" o "¿Cuál es la mejor manera de...?" -- útil, pero no muy
distinto de lo que el propio modelo de embeddings (`rrhh_bot.py`) ya
generaliza sin ayuda. Un motor de chat completo (Ollama, OpenAI, Claude,
Gemini) sigue siendo mejor para variancia genuina (otra estructura de
oración, sinónimos, registro distinto) -- un paráfrasis local pequeño no
los reemplaza, como mucho los complementa para variantes triviales y
gratuitas.

## Cómo quedó implementado

`entrenar.py` trata `local` como un motor aparte en `sugerir_frases()`
(`_sugerir_local()`), con su propio camino de código -- no reusa
`MOTORES[motor]["fn"]`, porque un modelo de paráfrasis no es de chat: toma
la pregunta original directamente y genera por *beam search*
(`num_return_sequences`), no texto libre a partir de un prompt.

Cada candidata generada se filtra antes de imprimirse para revisión:
se descarta si no comparte **ninguna** palabra clave con la pregunta
original, reutilizando `_palabras_clave()` de `rrhh_bot.py` (la misma
lógica ya construida esta sesión para la revisión sintáctica de preguntas
ambiguas, en vez de duplicarla). Esto habría descartado automáticamente el
caso de "opinión" de arriba -- y, en la corrida real de abajo, lo hizo.

Se añadió `sentencepiece` a `requirements.txt` (necesario para el tokenizer
de mT5). El modelo (~300 MB) se descarga y cachea igual que los otros dos
modelos preentrenados del proyecto (ver "Primera vez" en
`MODEL_TRAINING.md`) -- ninguna dependencia nueva más allá de
`sentencepiece`, nada de Ollama ni cuenta paga.

### Resultado de la primera corrida real (`--augmentar --motor local`)

El filtro funcionó para el caso que lo motivó: de las 3 variantes generadas
para "¿Cuándo pagan la nómina?", las 2 que decían "opinión" en vez de
"nómina" se descartaron; sobrevivió 1, aunque mezclada ("¿Cuándo puedo pagar
la opinión sobre la nomina?") -- conserva la palabra clave, pero la frase
sigue sin tener sentido. El filtro atrapa la sustitución completa de la
palabra de dominio, no cualquier corrupción -- exactamente la limitación ya
anotada arriba, confirmada en uso real.

También salieron casos nuevos que el filtro no estaba pensado para atrapar:

- Para EPS, el modelo generó `"¿Cómo puedo convertirme en un familiar en mi
  EP?"` -- cambia el verbo completo ("incluyo" por "convertirme en", un
  significado distinto) pero sobrevive el filtro porque comparte la palabra
  "familiar" con el tema original. El filtro revisa sustantivos de dominio
  compartidos, no que el verbo/acción siga siendo el mismo.
- Para vacantes internas, alucinó un país: `"¿Hay vacantes internas en la
  India?"` -- nada en la pregunta original sugiere eso.

Confirma lo ya dicho: el filtro reduce el riesgo de corrupción obvia, no lo
elimina. Sigue haciendo falta revisar cada sugerencia antes de añadirla a
`faq_rrhh.json` -- con más cuidado que con un motor de chat.

### Hallazgo aparte, no relacionado con el parafraseador: superposición entre temas

Esa misma corrida recalibró el umbral contra el `faq_rrhh.json` de entonces
(47 frases) y reportó superposición entre temas: peor similitud dentro de un
mismo tema 0.279, peor similitud entre temas distintos 0.902, umbral
sugerido 0.59 (por debajo del `THRESHOLD` actual de 0.65). Investigado
después (a pedido): de 1029 pares de frases de temas distintos, solo 3
superaban el `THRESHOLD` actual, concentrados en dos pares de temas, no un
problema generalizado.

- **Nómina ↔ prima (0.902):** `"¿Cuándo pagan la nómina?"` y `"¿Cuándo pagan
  la prima?"` -- mismo molde de pregunta, solo cambia el sustantivo.
- **EPS inclusión ↔ EPS traslado (0.668):** `"¿Cómo agrego un beneficiario a
  mi EPS?"` y `"¿Cómo me traslado de EPS?"` -- acciones relacionadas pero
  distintas, superposición más leve.

**Por qué no se tocó `THRESHOLD`:** el umbral solo decide si una coincidencia
es lo bastante segura para confiar en ella; no distingue entre dos temas que
compiten con puntajes altos. Si "nómina" y "prima" compiten a 0.902, ningún
valor razonable de `THRESHOLD` evita que gane el equivocado -- bajarlo a
0.59 no habría arreglado la confusión, solo habría hecho que coincidencias
más débiles (pero correctas) en otros temas también se dieran por buenas.
Esto es un problema de **contenido** (dos preguntas demasiado parecidas),
no de **calibración**.

**Lo que sí se hizo:** reformular las frases involucradas para reducir el
parecido textual, no por cosmética sino apuntando a lo que sí distingue cada
tema (nómina se paga mensual, prima es semestral):

| Tema | Antes | Después |
|---|---|---|
| `nomina` | `¿Cuándo pagan la nómina?` | `¿En qué fecha me consignan la nómina cada mes?` |
| `prima` | `¿Cuándo pagan la prima?` | `¿En qué mes del semestre cae el pago de la prima?` |
| `eps-inclusion` | `¿Cómo agrego un beneficiario a mi EPS?` | `¿Cómo agrego un familiar como beneficiario de mi EPS?` |
| `eps-traslado` | `¿Cómo me traslado de EPS?` | `¿Cómo cambio de entidad de EPS?` |

Resultado, verificado empíricamente (no solo supuesto) tras cada cambio:
EPS inclusión/traslado bajó de 0.668 a 0.623 -- ya no supera `THRESHOLD`.
Nómina/prima bajó de 0.902 a 0.725 en dos rondas de reformulación, con
rendimientos decrecientes (0.902 → 0.734 → 0.725) -- se detuvo ahí en vez
de seguir adivinando reformulaciones. Pares que superan `THRESHOLD`: de 3 a
1.

**Por qué quedó un residual (en ese momento):** "¿cuándo me pagan X?" es,
para el modelo de embeddings, un mismo *tipo* de pregunta sin importar qué
sea X -- el parecido no es un defecto de redacción, es que la pregunta
genuinamente tiene la misma forma en los dos temas. Más reformulación no lo
iba a bajar mucho más.

Verificado en ese momento: pytest 48/48, Node 10/10, Playwright 20/21 (la
misma falla preexistente y no relacionada de siempre). `THRESHOLD` en
`rrhh_bot.py` sigue en 0.65, sin tocar.

## Segunda capa: desempate por palabras cuando dos temas casi empatan

El residual de arriba no era solo teórico. Probado con consultas parecidas a
lo que escribiría alguien real (no las frases exactas del FAQ):

```text
'cuánta prima me pagan este semestre'  -> nómina 0.681, prima 0.671  (¡MAL -- gana nómina!)
'cuánto me pagan de nómina este mes'   -> nómina 0.752, prima 0.736  (bien, pero por poco)
'cuánto me pagan este mes'             -> prima  0.719, nómina 0.716 (ambiguo de verdad, sin pista léxica)
```

El primer caso es un error real y demostrable, no hipotético: una pregunta
que dice "prima" explícitamente la contesta nómina. Reformular más las
frases del FAQ ya había dado rendimientos decrecientes (sección anterior);
en vez de seguir por ahí, se añadió una capa adicional en `rrhh_bot.py`
-- sin datos de entrenamiento nuevos, sin tocar el modelo de embeddings --
que actúa solo cuando dos temas de entradas distintas quedan casi empatados
(`MARGEN_DISPUTA = 0.05`) en un resultado que de por sí ya es confiable
(`confianza >= THRESHOLD`):

- `_desempatar_por_palabras()` calcula, para cada tema en disputa, las
  palabras que lo distinguen de los demás en disputa (restando las que
  comparten) -- p. ej. "nómina" le pertenece solo a nómina, "prima" y
  "semestral" solo a prima; "cuándo", "pagan", "mes" se restan por
  compartidas.
- Si el mensaje contiene una palabra distintiva de un único tema en disputa,
  gana ese tema sobre el que había elegido el modelo semántico.
- Si no contiene ninguna, o contiene palabras distintivas de más de un tema
  (igual de empatadas léxicamente), se respeta el resultado semántico
  original -- esta capa solo actúa con una señal clara e inequívoca, nunca
  adivina.

Resultado, verificado contra el modelo real (no solo con el mock de los
tests): el primer caso de arriba pasó de "nómina" (mal) a "prima" (bien); el
segundo se mantuvo en "nómina" pero ahora de forma deliberada, no por un
margen de 0.016; el tercero -- genuinamente ambiguo, sin "nómina" ni "prima"
en el texto -- se dejó tal cual, sin forzar una respuesta.

Cuatro unit tests nuevos en `tests/test_rrhh_bot.py`, contra un fixture
dedicado (`tests/fixtures/faq_empate_test.json`, dos temas que comparten
todo excepto una palabra cada uno) con `cos_sim` mockeado para forzar
puntajes empatados exactos: el desempate corrige cuando hay una palabra
distintiva clara, respeta el resultado semántico cuando no hay ninguna o
hay más de una, y nunca se activa si los temas no estaban realmente
empatados -- cubre tanto el camino feliz como las dos formas en que podría
sobre-actuar.

Verificado después de este cambio: pytest 52/52, Node 10/10, Playwright
20/21 (la misma falla preexistente). `THRESHOLD` sigue sin tocarse --
`MARGEN_DISPUTA` es una constante nueva y separada, no una reinterpretación
de la existente.

## Reproducir esta prueba

```powershell
pip install sentencepiece
python -c "
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
tok = AutoTokenizer.from_pretrained('p-serna/mt5-small-spanish-paraphraser')
model = AutoModelForSeq2SeqLM.from_pretrained('p-serna/mt5-small-spanish-paraphraser')
ids = tok('¿Cuándo pagan la nómina?', return_tensors='pt')
salida = model.generate(**ids, max_length=64, num_beams=5, num_return_sequences=3, no_repeat_ngram_size=2)
for s in salida:
    print(tok.decode(s, skip_special_tokens=True))
"
```
