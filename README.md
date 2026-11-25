# Prebel Conecta

Demo del portal del colaborador. La página (`dist/`) funciona sola: perfil, trámites
y un buscador por palabras clave. Si además está corriendo la API local (`model/`),
el mismo buscador compara la pregunta con el FAQ usando dos modelos preentrenados
(similitud semántica y sentimiento) y muestra la comparación en la página.

No es un modelo que redacta respuestas. Elige la entrada del FAQ más parecida, o
pide escribir a RRHH cuando la similitud no alcanza.

Esta demo tiene varios componentes (portal, capa semántica, dos canales de
WhatsApp). Para el mapa completo, los requisitos mínimos en conjunto y la
provisión de cuentas/accesos, ver [`SETUP_AND_DEPLOY.md`](SETUP_AND_DEPLOY.md).
Para el detalle de **qué camino toma cada pregunta** según por dónde entra
(portal, WhatsApp local, WhatsApp/chat por n8n), ver [`FLUJOS.md`](FLUJOS.md).
Lo de abajo es el detalle de instalar y correr el portal localmente.

## Qué hace el portal

Datos ficticios, guardados en el navegador (`localStorage`). Los perfiles salen de
`model/empleados_mock.json` (también ficticio — ver R1/R4 en `CONSTITUTION.md`):

- **Valentina Ruiz**, analista administrativa (nómina administrativa, CC). Ve el
  recurso de ergonomía en oficina.
- **Mateo Ríos**, operario de empaque (nómina operativa, CC). Ve la reposición de
  protección personal.
- **Camila Torres**, impulsadora comercial (nómina de impulso y mercadeo, PPT).
- **Andrés Castro**, técnico de mantenimiento (nómina operativa, CE).

Entre los tres cubren los tres tipos de documento (CC/CE/PPT) y los tres tipos de
nómina (administrativa/operativa/impulso y mercadeo) que distinguen varios trámites
reales de RRHH. Cada perfil tiene su saldo de vacaciones, su prima acumulada, su
nómina de ejemplo y sus solicitudes. Cambiar el perfil recarga la página.

Desde **Mi espacio** se puede:

- Consultar el saldo y proyectarlo a 1, 3, 6 o 12 meses. La proyección suma 1,25
  días por mes y supone que no se piden más vacaciones. Es una regla fija de la
  demo, no la calcula el modelo.
- Pedir vacaciones (días hábiles, de lunes a viernes). Avisa si las fechas se
  cruzan o si superan el saldo. La solicitud queda pendiente y se puede cancelar.
- Ver un comprobante de los tres últimos períodos y descargarlo como `.txt`.
- Generar un certificado laboral con salario o sin salario, y descargarlo.
- Revisar el historial en **Mis solicitudes**.
- Abrir trámites con Nómina o con Bienestar y RSE: inclusión y traslado de EPS,
  los cuatro tipos de crédito de bienestar (educación/cómputo, mascotas, salud,
  vivienda), consulta de prima, reporte de incapacidad, retiro de cesantías y
  traslado de pensión a Colpensiones. Cada uno abre un formulario mínimo y, al
  enviarlo, queda pendiente en **Mis solicitudes**; la confirmación siempre
  nombra el equipo responsable (p. ej. "Bienestar y RSE"), nunca a una persona
  real — ver R1 en `CONSTITUTION.md`.
- Abrir **Preguntas frecuentes**. El listado mezcla las respuestas del portal con
  las de `model/faq_rrhh.json` (15 temas: vacaciones, certificado, incapacidad,
  nómina, datos personales, vacantes internas, EPS, créditos, prima y cesantías).
  Los textos con `[X]`, `[sistema]` o `[portal]` son marcadores a propósito.

Los trámites se abren en un cuadro de diálogo. La respuesta del modelo no: queda
en la sección **Resultado del modelo**, debajo del buscador. Si la coincidencia
tiene una ruta, esa sección muestra un botón que sí abre el diálogo del trámite.

## Cómo se responde una pregunta

El buscador tiene dos caminos.

**Palabras clave (siempre, sin API).** Al escribir, `dist/app.js` compara las
palabras con los trámites y con las preguntas del FAQ, sin acentos, y muestra
hasta tres sugerencias. Enter sobre una sugerencia abre ese trámite o esa
pregunta. Si no hay ninguna, el texto dice que no hubo coincidencia.

**Modelo (solo si no hay sugerencia y se pulsa Enter).** Ahí se llama a
`http://127.0.0.1:5000/reply`. El cuadro compara las dos respuestas:

| Campo en pantalla | Qué es |
|---|---|
| Coincidencia rápida | La mejor sugerencia por palabras clave, o "Sin coincidencia rápida" |
| Respuesta del modelo | El texto del FAQ elegido, o el mensaje de respaldo |
| Nivel de profundidad | Similitud con la pregunta del FAQ más cercana, en porcentaje |
| Sentimiento detectado | Negativo, neutral o positivo, con su propia confianza |
| Área | Gestión Humana, Nómina o Contratación, cuando la entrada del FAQ la trae |

Si la API no responde en 1,5 segundos, el cuadro igual aparece: la respuesta es
el mensaje de respaldo y confianza y sentimiento dicen "No disponible (API local
no activa)".

`/reply` ya devuelve algunos campos más (`guia`, `tipo`, `capa` -- ver
siguiente sección y [`FLUJOS.md`](FLUJOS.md)) que este cuadro todavía no
muestra; agregarlos a la UI queda para una próxima ronda.

## Cómo funciona el modelo

`model/rrhh_bot.py` carga `model/faq_rrhh.json` al arrancar. Cada tema tiene
varias formas de preguntarlo, una respuesta, y a veces una ruta y un área.

1. **Similitud.** El modelo `paraphrase-multilingual-MiniLM-L12-v2` convierte la
   pregunta del colaborador y todas las frases del FAQ en vectores. Se compara
   con similitud del coseno y se queda con la frase más alta.
2. **Corte.** Si esa similitud es menor que **0,65**, no se usa esa respuesta.
   Se devuelve el texto de respaldo del JSON: no hay una respuesta segura y hay
   que escribir a `rrhh@tuempresa.com`. Por eso una pregunta cercana pero distinta
   (por ejemplo "no me han pagado horas extras", que ronda 0,60 con nómina) no
   se contesta con el desprendible de pago. Una paráfrasis real del FAQ, como
   "¿cuándo pagan la nómina?", suele quedar por encima de 0,65.
3. **Sentimiento.** En paralelo, `nlptown/bert-base-multilingual-uncased-sentiment`
   clasifica el mensaje de 1 a 5 estrellas: 1–2 negativo, 3 neutral, 4–5 positivo.
   No cambia la respuesta; solo se muestra en el cuadro.

Por encima de `RRHHBot`, `model/orquestador.py` decide si esa respuesta
semántica ya basta o si hace falta escalar: con más de 95% de similitud se
confía en ella directo; entre 75% y 95% se usa tal cual; por debajo de 75%
(o si quien llama pide seguir buscando), antes de escalar de verdad revisa
si una pregunta parecida ya la resolvió el conector LLM antes
(`model/rag_retroalimentacion.py`, umbral 85%) y la reusa sin volver a
llamarlo; si no hay nada parecido, sí escala a un conector LLM
intercambiable (hoy, vía MCP -- apagado por defecto, así que esto no
cambia nada si no se configura). El detalle completo de esa cadena, con
diagrama, está en [`FLUJOS.md`](FLUJOS.md) y en `CONSTITUTION.md` (R8/R9).

`POST /reply` recibe `{"text": "...", "seguir": false}` (`seguir` es
opcional) y responde con `reply`, `ruta`, `area`, `confianza`,
`sentimiento`, `guia`, `tipo` y `capa` -- los últimos tres son aditivos,
`dist/app.js` todavía no los usa (ver `FLUJOS.md` para el contrato
completo). Un texto vacío también devuelve el respaldo.

La primera vez, los dos modelos se descargan de Hugging Face (~1 GB) y quedan en
caché. Las pruebas automáticas no los cargan: usan sustitutos.

Ese umbral de 0,65 y los embeddings del FAQ se recalibran con
`model/entrenar.py` — qué configuración usa hoy, cómo volver a calibrarlo, y
cómo generar frases nuevas del FAQ con cualquier motor de IA (Ollama, OpenAI,
Claude o Gemini) está en [`MODEL_TRAINING.md`](MODEL_TRAINING.md). Si en vez
de un motor de chat te preguntas por un modelo de paráfrasis local más chico,
la exploración (y por qué no se adoptó tal cual) está en
[`MODEL_TUNING.md`](MODEL_TUNING.md).

## Canal de WhatsApp (opcional, solo para pruebas locales)

`model/whatsapp_service.py` es un canal adicional para el mismo `RRHHBot` que
usa `rrhh_api.py`, pero por WhatsApp en vez de por el navegador: recibe los
webhooks de un entorno compatible con la WhatsApp Cloud API, responde con
`RRHHBot.match()` y envía la respuesta de vuelta a esa misma API. No
reemplaza `rrhh_api.py` ni depende de él; es un segundo consumidor de
`RRHHBot`, independiente.

Para probarlo localmente hace falta un entorno que hable ese protocolo. El
repositorio hermano `whatsapp-emulator/` (en `C:\PyProje\PyBot\whatsapp-emulator`,
**fuera de este repositorio** — no es parte del entregable, solo un auxiliar
de pruebas hasta tener un entorno de pruebas real de Meta) imita esa API.

1. Copia `.env.example` a `.env` (ya está en `.gitignore`) y ajusta los
   valores si quieres, o deja los que coinciden con un emulador recién
   arrancado.
2. Arranca el emulador (en su propia carpeta, con Node.js 18+):

   ```powershell
   cd C:\PyProje\PyBot\whatsapp-emulator
   $env:WEBHOOK_URL = "http://localhost:3000/webhook"
   $env:VERIFY_TOKEN = "prebel-conecta-dev"
   $env:APP_SECRET = "prebel-conecta-dev-secret"
   $env:PHONE_NUMBER_ID = "100000000000001"
   node server.js
   ```

3. Arranca el canal (desde `prebel-conecta/`, con el `.venv` activo):

   ```powershell
   python model\whatsapp_service.py
   ```

4. Abre `http://localhost:4010`, ve a **Config** y usa **Verificar webhook**
   (confirma que `/webhook` responde el `hub.challenge`). Luego escríbele al
   bot desde la interfaz tipo teléfono: la pregunta llega por webhook, pasa
   por `RRHHBot` y la respuesta vuelve a aparecer en esa misma interfaz.

Los parámetros de conexión y secretos (`WA_GRAPH_URL`, `WA_PHONE_NUMBER_ID`,
`WA_ACCESS_TOKEN`, `WA_VERIFY_TOKEN`, `WA_APP_SECRET`, `WA_SERVICE_PORT`) se
leen de variables de entorno o de `.env` — nunca están hardcodeados. Para
apuntar a un entorno de pruebas real de Meta más adelante, solo hay que
cambiar esos valores (y el `WA_GRAPH_URL` a `https://graph.facebook.com`); el
código de `whatsapp_service.py` no cambia.

## Canal de WhatsApp con n8n + cadena de 3 niveles (opcional, servidor de pruebas)

`n8n/` es un canal adicional (WhatsApp y, ahora, una burbuja de chat en el
portal) que corre en el servidor del equipo: un "cerebro" compartido y tres
"puertas" (emulador de WhatsApp Cloud API, Evolution API para WhatsApp real,
y el portal vía una burbuja de chat).

El cerebro ya no es un sistema aparte: antes de redactar una respuesta con
IA a partir de los documentos oficiales de Prebel (RAG con Ollama, el
"Nivel 2, Agentic"), le pregunta primero a `model/rrhh_api.py` (el mismo
modelo que usa el portal) si tiene una respuesta segura del FAQ ficticio
(el "Nivel 1, ML", < 1 s) — y solo si no la tiene, sigue con el RAG. Junto
con su propio detector de saludo/menú ("Nivel 0, Predictivo"), los tres
niveles forman la cadena **propia de n8n**: barato y rápido primero, la IA
que redacta (más lenta, ~20 s) solo cuando hace falta.

Esta cadena es independiente de la que ahora orquesta
`model/orquestador.py` del lado de Python (ver "Cómo funciona el modelo"
arriba): n8n solo lee `confianza` y `reply` de `/reply`, así que para n8n
el comportamiento es el mismo de siempre. Las dos cadenas pueden, más
adelante, conectarse (este mismo cerebro puede servir como backend del
conector LLM de Python, vía MCP) pero hoy corren por separado. El mapa
completo de los dos caminos, lado a lado, está en
[`FLUJOS.md`](FLUJOS.md); el detalle de la cadena propia de n8n sigue en
"El encadenamiento de 3 niveles" de `CONSTITUTION.md` y en `n8n/README.md`.

Para que el cerebro (en el servidor del equipo) pueda llamar a
`model/rrhh_api.py`, este se empaqueta con el `Dockerfile` de esta carpeta y
se despliega junto a n8n y Ollama, en su misma red privada — nunca expuesto
al público. Qué hace cada flujo, cómo se importa, cómo desplegar ese
contenedor y qué datos quedan fuera de git está en
[`n8n/README.md`](n8n/README.md).

**Nota técnica — n8n local vs. real para pruebas:** se espera usar tanto
una instancia real de n8n (la del servidor del equipo) como una local (con
Docker, imagen oficial [`n8nio/n8n`](https://hub.docker.com/r/n8nio/n8n))
para probar cambios a estos flujos — **a discreción de quien desarrolla o
de SDET**, según qué se esté verificando. La local alcanza para validar que
un flujo importa bien y que el Tier 1/Tier 2 se encadenan correctamente
(incluido el caso en que el Tier 1 falla y cae con gracia al Tier 2); la
real es la única forma de validar el RAG completo (Ollama, documentos
reales) y la entrega real por WhatsApp. Ninguna reemplaza a la otra. Ver
`SETUP_AND_DEPLOY.md` §4 y la sección "Probar los flujos en un n8n local"
de [`n8n/README.md`](n8n/README.md) para el procedimiento.

## Estructura

- `dist/` — sitio estático (HTML, CSS y JS). No tiene paso de compilación.
- `model/` — `rrhh_bot.py` (capa ML/semántica), `orquestador.py` (decide
  predictivo/ML/LLM por encima de `rrhh_bot.py`, ver [`FLUJOS.md`](FLUJOS.md)),
  `conectores.py` (conector LLM intercambiable, vía MCP),
  `configuracion.py` + `arquitectura.json` (umbrales editables de la
  cadena), `retroalimentacion.py` (cola de preguntas que el LLM resolvió y
  las capas anteriores no tenían, para revisión manual),
  `rag_retroalimentacion.py` (reusa esas respuestas por similitud antes de
  volver a llamar al LLM, ver [`FLUJOS.md`](FLUJOS.md)), `rrhh_api.py`
  (Flask en `127.0.0.1:5000`, consumidor desde el navegador),
  `whatsapp_service.py` (Flask en `WA_SERVICE_PORT`, consumidor desde un
  entorno compatible con la WhatsApp Cloud API — ver sección **Canal de
  WhatsApp** más abajo), `faq_rrhh.json` (contenido del FAQ),
  `empleados_mock.json` (los 4 perfiles ficticios, única fuente de los
  datos de persona — `catalogo.py` solo los lee y exporta) y `entrenar.py`
  (cachea embeddings y recalibra el umbral de similitud — ver
  [`MODEL_TRAINING.md`](MODEL_TRAINING.md)).
- `n8n/` — canal de WhatsApp y burbuja de chat del portal en n8n (flujos
  exportados + scripts de la base de conocimiento). Ver
  [`n8n/README.md`](n8n/README.md).
- `Dockerfile` + `docker-compose.yml` — empaquetan la cadena completa
  (`rrhh_api.py` + `orquestador.py` + el conector) como un solo monolito
  desplegable (`docker compose up --build`, puerto `5000`), o para
  desplegarlo junto a n8n y Ollama como Nivel 1 de su propia cadena (ver
  más abajo); no se usan para correr el portal localmente, eso sigue
  siendo `iniciar-conecta.ps1`.
- `catalogo.py` — escribe `dist/catalogo.js` y `dist/faq.js` desde
  `model/empleados_mock.json` y `model/faq_rrhh.json`.
- `iniciar-conecta.ps1` — levanta la API y el sitio con un solo comando.
- `tests/` — unit tests de Python (pytest) y de JS (`node:test`); `e2e/` — e2e
  con Playwright. Ver la sección **Tests** más abajo.
- `.specs/` (local, no versionado) — documentos reales de RRHH de Prebel, usados
  solo como referencia al redactar contenido ficticio. Nunca se lee en tiempo de
  ejecución ni desde las pruebas — ver R1 en `CONSTITUTION.md`.
- `.github/workflows/pages.yml` — publica solo `dist/` en GitHub Pages en cada
  push a `main`. Esa URL no incluye el modelo: el navegador de quien la abre
  sigue buscando la API en su propio `127.0.0.1`.

## Requisitos de desarrollo

| Herramienta | Para qué | Notas |
|---|---|---|
| **Python 3.10+** con `pip` y `venv` | API (`model/`), `catalogo.py`, `entrenar.py`, unit tests de Python | Probado con 3.15. |
| **Node.js 18+** con `npm` y `npx` | Unit tests de JS (`node --test`, nativo) y E2E con Playwright | No hace falta para correr el sitio ni la API. |
| **PowerShell** (Windows) | `iniciar-conecta.ps1` | Incluido en Windows; también corre en PowerShell 7+ multiplataforma. |
| **Git** | Clonar y versionar | `prebel-conecta/` es su propio repositorio, independiente de la carpeta que lo contiene. |
| Navegador | Abrir la demo | Playwright instala su propio Chromium para los e2e (`npx playwright install`); no usa el navegador del sistema. |

No hace falta build tools de C/C++ ni GPU. La primera vez que corras la
API sí se descargan ~1 GB de pesos de modelo desde Hugging Face (ver más abajo).

Ninguna de estas herramientas hace falta para lo de arriba: Ollama (local) u
OpenAI/Claude/Gemini (con su clave de API) son **solo** para `entrenar.py
--augmentar`, que es opcional — ver [`MODEL_TRAINING.md`](MODEL_TRAINING.md).
Tampoco hace falta nada extra para el conector LLM del orquestador (ver
[`FLUJOS.md`](FLUJOS.md)): la dependencia `mcp` ya viene en
`requirements.txt`/`requirements-dev.txt`, y sin la variable de entorno
`LLM_CONECTOR` configurada, el orquestador nunca intenta usarlo.
Docker tampoco hace falta para correr el portal o la API — es aparte, para
levantar el monolito contenerizado (`docker-compose.yml`, ver `Dockerfile`)
y para probar el canal n8n con una instancia local (ver sección **Canal de
WhatsApp con n8n** más abajo). El detalle completo de requisitos de **todos** los componentes,
incluida la provisión de cuentas, está en
[`SETUP_AND_DEPLOY.md`](SETUP_AND_DEPLOY.md).

## Setup

Desde `prebel-conecta/` (esta carpeta es un repositorio Git independiente):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

python model\entrenar.py
```

Esto instala todo lo necesario para correr la API, `catalogo.py` y los unit tests
de Python. Node.js solo hace falta si vas a correr los unit tests de JS o los e2e
(ver **Tests**) — no tiene instalación aparte, se usa el Node.js del sistema.

Ese último `python model\entrenar.py` es opcional pero recomendado la primera
vez: descarga y cachea los dos modelos preentrenados (~1 GB) y deja listo el
caché de embeddings del FAQ, para que el primer `.\iniciar-conecta.ps1`
o `python model\rrhh_api.py` ya no tenga que esperar esa descarga. Si lo
saltas, la API igual funciona — descarga los modelos ella misma en su propio
primer arranque. Detalle completo en [`MODEL_TRAINING.md`](MODEL_TRAINING.md).

## Run

**Opción rápida (recomendada):** desde `prebel-conecta/`:

```powershell
.\iniciar-conecta.ps1                  # usa el puerto 8080
.\iniciar-conecta.ps1 -Puerto 8090      # puerto alternativo
.\iniciar-conecta.ps1 -Verbose          # muestra cada intento de conexión al backend
```

Levanta la API en `http://127.0.0.1:5000`, sirve la página en `http://127.0.0.1:<puerto>`
y la abre en el navegador. Al terminar de arrancar imprime las URLs y el estado del
backend; si no responde en 30s, revisa `backend.log` (se genera junto a este script).
Presiona Ctrl+C para detener backend y sitio.

**Manual (dos terminales):**

```powershell
# Terminal 1 — backend
python model\rrhh_api.py                      # http://127.0.0.1:5000

# Terminal 2 — sitio estático
python -m http.server 8080 --directory dist   # http://127.0.0.1:8080
```

## Regenerar los datos de la demo

Si cambias `model/faq_rrhh.json` o `model/empleados_mock.json`:

```powershell
python catalogo.py
```

Esto regenera `dist/catalogo.js` y `dist/faq.js`.

## Tests

Las reglas completas (qué cubre cada suite, por qué, y qué significa "verde")
están en [`CONSTITUTION.md`](CONSTITUTION.md) — esto es solo el cómo correrlas.

**Unit tests de Python** (rápidos, sin red, sin modelos reales):

```powershell
pip install -r requirements-dev.txt
pytest tests -v
```

**Unit tests de JS** (funciones puras de `dist/app.js`, sin navegador):

```powershell
node --test tests/js
```

**E2E con Playwright** (navegador real; la API local se simula, no hace falta
tenerla instalada ni corriendo):

```powershell
cd e2e
npm install
npx playwright install --with-deps chromium   # solo la primera vez
npx playwright test
```

Cada corrida deja un dashboard HTML en `e2e/playwright-report/` (resultado de
cada prueba, con sus trazas y capturas si falla). Para abrirlo (desde
`e2e/` -- `show-report` busca `playwright-report/` en el directorio actual):

```powershell
cd e2e
npx playwright show-report
```

No se versiona (está en `.gitignore`): se regenera en cada corrida.
