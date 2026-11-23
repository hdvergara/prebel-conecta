# Canal WhatsApp con n8n (Prebel – Gestión Humana)

Chatbot de Gestión Humana por WhatsApp, hecho en **n8n** con IA local (Ollama).
Responde **solo** con los documentos oficiales de Prebel y dice "no disponible"
cuando la pregunta no está en ellos.

> ⚠️ **Datos reales fuera de git.** Los documentos de Prebel (auxilios, créditos,
> nómina, glosario, tono) tienen nombres, correos, teléfonos y cifras internas.
> No se suben nunca: ni los `.md` originales, ni `data/kb.json` (las fichas que
> salen de ellos), ni `*.real.json` (el cerebro con nombres reales).

## La idea: un cerebro y dos puertas

```
WhatsApp real ──► Evolution API ──► [Puerta Evolution] ─┐
                                                         ├─► [Cerebro (IA)] ──► respuesta
Emulador Cloud API ─────────────► [Puerta Emulador] ────┘
```

- **Cerebro** (`03-cerebro-ia.json`): sub-flujo que recibe `pregunta` y devuelve
  la `respuesta` lista para WhatsApp. No sabe de qué canal viene la pregunta,
  así que las dos puertas reciben exactamente las mismas respuestas.
- **Puertas** (`01-puerta-emulador.json`, `02-puerta-evolution.json`): adaptadores.
  Reciben el mensaje, revisan que sea auténtico, marcan "leído", mandan el aviso
  *"Estoy buscando la información… ⏳"* (salvo en los saludos), le preguntan al
  cerebro y devuelven la respuesta.

### Cómo responde el cerebro (RAG)

1. **Saludo o menú** ("hola", "menú", "ayuda"…) → responde el menú al instante, sin IA.
   La lista de saludos vive **solo** en el nodo *Detectar saludo (lista única)*.
   Las puertas la consultan llamando al cerebro con `modo = clasificar`.
2. **Embedding** de la pregunta con `embeddinggemma` (Ollama).
3. Compara con las fichas de la Data Table `prebel_kb` (similitud coseno,
   umbral 0,30, máximo 3 fichas).
4. Si ninguna ficha se parece → mensaje oficial de "no disponible", sin IA.
5. Si hay fichas → la IA (Ollama) redacta la respuesta solo con esas fichas.
6. Agrega la línea *Fuente: documento › sección* y el aviso de que es una IA.

Diferencia con `model/rrhh_bot.py`: ese bot **elige** una respuesta escrita del
FAQ. Este **redacta** la respuesta a partir de los documentos completos de Prebel.
Son dos enfoques que se pueden comparar.

## Archivos

| Archivo | Qué es |
|---|---|
| `workflows/01-puerta-emulador.json` | Puerta para el emulador de WhatsApp Cloud API (firma HMAC y token) |
| `workflows/02-puerta-evolution.json` | Puerta para Evolution API (WhatsApp real, cabecera secreta en el webhook) |
| `workflows/03-cerebro-ia.json` | Cerebro con los contactos cambiados por marcadores `[Nombre]` y `[teléfono de Gestión Humana]` |
| `scripts/ingesta.py` | Parte los documentos de Prebel en fichas → `data/kb.json` |
| `scripts/cargar_kb.py` | Calcula los embeddings y carga las fichas en la Data Table de n8n |
| `scripts/exportar_flujos.py` | Exporta los tres flujos desde n8n y genera la versión sin datos personales (solo para el servidor CORE-LAB) |

## Cómo montarlo en otro n8n

Requisitos: n8n 2.x, Ollama con los modelos `embeddinggemma` y el modelo de
redacción (hoy `gemma4:e2b`), y el nodo comunitario `n8n-nodes-evolution-api`
(solo para la puerta de Evolution).

Los comandos se corren desde la carpeta `n8n/`.

1. **Fichas:** con los documentos reales en una carpeta que no esté en git
   (en este repo, `.specs/`, ignorada por `.gitignore`):
   ```bash
   PREBEL_DOCS_DIR=../.specs python3 -I scripts/ingesta.py
   ```
2. **Data Table:** crea en n8n una tabla `prebel_kb` con las columnas
   `ficha_id`, `documento`, `seccion`, `texto` y `embedding` (todas texto), y cárgala:
   ```bash
   N8N_API_URL=https://tu-n8n N8N_API_KEY=... OLLAMA_URL=http://localhost:11434 \
     python3 -I scripts/cargar_kb.py <ID_DE_LA_TABLA>
   ```
3. **Importa los flujos** (menú *Import from File*): primero el cerebro, luego las puertas.
4. **Ajusta después de importar:**
   - En el cerebro: el nodo *Leer fichas* (elige tu tabla), la URL de Ollama en
     *Embedding de la pregunta*, la credencial de *Modelo Ollama* y los marcadores
     `[Nombre]` / `[teléfono de Gestión Humana]` en los avisos.
   - En cada puerta: los dos nodos *¿Es saludo?* y *Preguntar al cerebro* (elige
     el cerebro importado) y las credenciales.
5. **Credenciales** (se crean a mano; sus valores nunca van al repo):
   - Emulador: `Crypto` (secreto HMAC del emulador) y `Bearer Auth` (token).
   - Evolution: `Evolution API` (instancia) y `Header Auth` (cabecera secreta del webhook).
   - Ollama: credencial de Ollama apuntando a tu servidor.

## Dónde corre y por qué este modelo

Los dos canales (WhatsApp real por Evolution y el emulador) usan **el mismo
cerebro y la misma IA local**. Nada se manda a servicios de IA externos: los
documentos de Prebel y las preguntas de los empleados no salen del servidor.

**Servidor (entorno de pruebas del equipo):**

| Recurso | Valor | Qué implica |
|---|---|---|
| Máquina | Nube, procesador ARM64 de 4 núcleos | Sin tarjeta gráfica (GPU): la IA corre en el procesador, despacio |
| Memoria RAM | 23 GB, compartida con n8n, bases de datos y otros servicios | Cabe un modelo pequeño o mediano a la vez, no uno grande |
| Disco | 96 GB, ~80 % usado | Cada modelo nuevo ocupa de 3 a 10 GB; hay que elegir pocos |
| Orquestación | Coolify (Docker) + n8n 2.x + Ollama | Todo se despliega como contenedores |

**Modelos en uso:**

- `embeddinggemma` (0,6 GB): convierte textos en "coordenadas" para buscar
  las fichas parecidas. Tarda ~0,4 s.
- `gemma4:e2b` (4,6 GB): redacta la respuesta.

**Por qué `gemma4:e2b`:** comparamos tres modelos con las mismas 5 preguntas,
las mismas fichas y el mismo prompt (2026-11-23):

| Modelo | Tamaño | Tiempo por respuesta | Resultado |
|---|---|---|---|
| `gemma4:e4b` (el anterior) | 9,6 GB | 48–69 s | Muy bueno, pero el doble de lento; a veces se cortaba por largo |
| **`gemma4:e2b` (elegido)** | 4,6 GB | **20–26 s** | Mismas cifras y requisitos; buen español; respeta el formato de WhatsApp |
| `gemma3:4b` | 3,4 GB | 39–62 s | Más lento y usa negritas dobles que WhatsApp no muestra |

Modelos más grandes (26B o 31B) no caben en la RAM disponible. Usar una IA
en la nube sería mucho más rápido, pero los documentos y las preguntas
saldrían del servidor; para el MVP se decidió mantenerlo local.

**Tiempos que ve el usuario:**

- Saludo o "no disponible": 1–3 s.
- Respuesta con IA: ~16–26 s. La primera después de un rato sin uso puede
  tardar 1–2 min más mientras el modelo se carga en memoria. Por eso el bot
  manda primero el aviso "buscando".
- El servidor procesa **una pregunta con IA a la vez**: si llegan 5 juntas,
  la quinta espera a las otras cuatro. Sirve para una demo, no para muchos
  usuarios simultáneos.

## Cómo se compara con el bot de `model/`

| | `model/rrhh_bot.py` (portal) | Canal n8n (este) |
|---|---|---|
| Cómo responde | **Elige** la entrada del FAQ más parecida (MiniLM, umbral 0,65) | **Busca** fichas de los documentos reales (embeddinggemma, umbral 0,30) y la IA **redacta** con ellas |
| Fuente | `model/faq_rrhh.json` (contenido ficticio con marcadores) | Documentos oficiales de Prebel (fuera de git) |
| Velocidad | < 1 s | 16–26 s |
| Si no sabe | Texto de respaldo, escribir a RRHH | Mensaje oficial "no disponible" |
| Extra | Sentimiento, área, ruta al trámite | Línea *Fuente: documento › sección* y aviso de IA |
| Dónde corre | PC del usuario (`127.0.0.1`) | Servidor del equipo |

Son complementarios: el FAQ es rápido y predecible para lo frecuente, y el
canal n8n responde preguntas abiertas con el detalle de los documentos.

### El emulador y `model/whatsapp_service.py`

Los dos hablan el mismo protocolo (WhatsApp Cloud API). Pero un emulador
manda los mensajes a **un solo** webhook: o a `whatsapp_service.py` o a la
Puerta Emulador de n8n, no a los dos a la vez. El emulador del servidor está
conectado a n8n; para probar `whatsapp_service.py` se usa un emulador local.

### Idea: un botón de chat en el portal

Es viable, con una condición: **no** conviene abrir el emulador desde el portal.

- El emulador es una herramienta de pruebas: todos los visitantes verían la
  misma conversación, y su pestaña *Config* deja cambiar la conexión.
- El portal está en HTTPS (GitHub Pages) y el emulador en HTTP: el navegador
  bloquea meterlo dentro de la página. Solo se podría abrir como enlace aparte.

La forma recomendada es una **tercera puerta, "Puerta Web"**: el nodo
*Chat Trigger* de n8n publica un chat por HTTPS que se puede incrustar en el
portal como una burbuja (`@n8n/chat`). Cada visitante tiene su propia
conversación y usa el mismo cerebro. Para cumplir `CONSTITUTION.md`:

- **R2 (static-first):** la burbuja debe cargarse aparte; si n8n no responde,
  el portal sigue funcionando igual.
- **R3 (sin secretos en el cliente):** la URL del chat es pública por diseño;
  se limita a los orígenes permitidos (opción *Allowed Origins* del Chat
  Trigger) y no lleva claves.
- **Capacidad:** como el servidor responde una pregunta con IA a la vez, la
  burbuja debería activarse solo para la demo (por ejemplo, con un parámetro
  en la URL), no para todo visitante de GitHub Pages.
