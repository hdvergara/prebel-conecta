# Ajuste de variancia del FAQ: ¿modelo de paráfrasis local?

Este documento registra una exploración puntual, no una decisión tomada: si
vale la pena **expandir la variancia de frases** del FAQ (más formas de
preguntar cada tema) usando un modelo de paráfrasis **pequeño y local**, en
vez de depender siempre de Ollama o de una API paga (`entrenar.py
--augmentar`, ver `MODEL_TRAINING.md`). La motivación de fondo es la misma
de siempre en este proyecto: capas baratas primero, motor pago solo cuando
de verdad hace falta -- aquí, específicamente, evitar que generar más
variancia de entrenamiento dependa de un modelo de chat completo (Ollama) o
de una cuenta paga, si un modelo chico y gratuito alcanza.

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

## Si se decide usarlo: cómo encajaría en `entrenar.py`

No implementado todavía -- queda pendiente de que se confirme que vale la
pena, dado lo anterior. Si se decide seguir adelante:

- Los 4 motores actuales (`MOTORES` en `entrenar.py`) comparten una interfaz
  de **chat**: `fn(prompt, modelo) -> texto`, donde el prompt ya incluye la
  instrucción completa ("Genera 3 formas distintas de preguntar..."). Un
  modelo de paráfrasis local no es de chat: toma la pregunta original
  directamente y genera por *beam search* (`num_return_sequences`), no por
  texto libre. Encajaría como un motor aparte en `sugerir_frases()` (p. ej.
  `motor == "local"`), con su propio camino de código en vez de reusar
  `MOTORES[motor]["fn"]`.
- Antes de imprimir cualquier sugerencia para revisión, filtrarla con una
  comprobación barata: ¿la paráfrasis conserva al menos una palabra clave
  del tema original (p. ej. "nómina", "cesantías", "EPS")? Esto habría
  descartado automáticamente el caso de "opinión" de arriba.
  **`rrhh_bot.py` ya tiene justo esa lógica** (`_palabras_clave()`,
  construida esta misma sesión para la revisión sintáctica de preguntas
  ambiguas) -- reutilizarla aquí evita duplicar la misma heurística dos
  veces en el proyecto.
- Requeriría añadir `sentencepiece` a `requirements.txt` (necesario para el
  tokenizer de mT5; no hacía falta hasta ahora porque `rrhh_bot.py` no usa
  ningún modelo basado en SentencePiece).
- El modelo (`p-serna/mt5-small-spanish-paraphraser`, ~300 MB) se
  descargaría y cachearía igual que los otros dos modelos preentrenados del
  proyecto (ver "Primera vez" en `MODEL_TRAINING.md`) -- ninguna descarga ni
  dependencia nueva más allá de `sentencepiece`.

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
