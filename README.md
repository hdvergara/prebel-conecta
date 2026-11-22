# Prebel Conecta

Demo del portal del colaborador. La página (`dist/`) funciona sola: perfil, trámites
y un buscador por palabras clave. Si además está corriendo la API local (`model/`),
el mismo buscador compara la pregunta con el FAQ usando dos modelos preentrenados
(similitud semántica y sentimiento) y muestra la comparación en la página.

No es un modelo que redacta respuestas. Elige la entrada del FAQ más parecida, o
pide escribir a RRHH cuando la similitud no alcanza.

## Qué hace el portal

Datos ficticios, guardados en el navegador (`localStorage`). Hay dos perfiles:

- **Valentina Ruiz**, analista administrativa. Ve el recurso de ergonomía en oficina.
- **Mateo Ríos**, operario de empaque. Ve la reposición de protección personal.

Cada perfil tiene su saldo de vacaciones, su nómina de ejemplo y sus solicitudes.
Cambiar el perfil recarga la página.

Desde **Mi espacio** se puede:

- Consultar el saldo y proyectarlo a 1, 3, 6 o 12 meses. La proyección suma 1,25
  días por mes y supone que no se piden más vacaciones. Es una regla fija de la
  demo, no la calcula el modelo.
- Pedir vacaciones (días hábiles, de lunes a viernes). Avisa si las fechas se
  cruzan o si superan el saldo. La solicitud queda pendiente y se puede cancelar.
- Ver un comprobante de los tres últimos períodos y descargarlo como `.txt`.
- Generar un certificado laboral con salario o sin salario, y descargarlo.
- Revisar el historial en **Mis solicitudes**.
- Abrir **Preguntas frecuentes**. El listado mezcla las respuestas del portal con
  las de `model/faq_rrhh.json` (vacaciones, certificado, incapacidad, nómina,
  datos personales y vacantes internas). Los textos con `[X]`, `[sistema]` o
  `[portal]` son marcadores a propósito.

Los trámites se abren en un cuadro de diálogo. La respuesta del modelo no: queda
en la sección **Resultado del modelo**, debajo del buscador. Si la coincidencia
tiene una ruta (`vacaciones`, `nomina` o `certificado`), esa sección muestra un
botón que sí abre el diálogo del trámite.

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

`POST /reply` recibe `{"text": "..."}` y responde con `reply`, `ruta`, `area`,
`confianza` y `sentimiento`. Un texto vacío también devuelve el respaldo.

La primera vez, los dos modelos se descargan de Hugging Face (~1 GB) y quedan en
caché. Las pruebas automáticas no los cargan: usan sustitutos.

## Estructura

- `dist/` — sitio estático (HTML, CSS y JS). No tiene paso de compilación.
- `model/` — `rrhh_bot.py`, `rrhh_api.py` (Flask en `127.0.0.1:5000`) y `faq_rrhh.json`.
- `catalogo.py` — escribe `dist/catalogo.js` y `dist/faq.js` desde los datos
  ficticios y desde `model/faq_rrhh.json`.
- `iniciar-conecta.ps1` — levanta la API y el sitio con un solo comando.
- `.github/workflows/pages.yml` — publica solo `dist/` en GitHub Pages en cada
  push a `main`. Esa URL no incluye el modelo: el navegador de quien la abre
  sigue buscando la API en su propio `127.0.0.1`.

## Setup

Desde `prebel-conecta/` (esta carpeta es un repositorio Git independiente):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

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

Si cambias `model/faq_rrhh.json` o los datos del catálogo en `catalogo.py`:

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
