# Prebel Conecta

Demo del portal del colaborador: un sitio estático (`dist/`) más un asistente de RRHH
que responde preguntas frecuentes con un modelo de lenguaje preentrenado (`model/`).

- `dist/` — sitio estático (HTML/CSS/JS). Se publica en GitHub Pages y funciona solo
  con un buscador por palabras clave si el backend no está corriendo.
- `model/` — bot de RRHH (`rrhh_bot.py`) y su API local (`rrhh_api.py`). Añaden al
  sitio respuestas por similitud semántica, nivel de confianza y sentimiento detectado.
- `catalogo.py` — genera `dist/catalogo.js` y `dist/faq.js` a partir de los datos de
  la demo y de `model/faq_rrhh.json`.
- `iniciar-conecta.ps1` — levanta backend + sitio con un solo comando. (Nota: el
  `bot.py` de la raíz del proyecto tiene su propio `iniciar.ps1`, sin relación con
  este; los nombres son distintos a propósito para no confundirlos.)

## Setup

Desde la raíz del proyecto (`c:\PyProje\PyBot`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

La primera vez que corras la API, `sentence-transformers` y el modelo de sentimiento
se descargan de Hugging Face (~1 GB en total) y quedan en caché para las siguientes.

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

Sin backend corriendo, el sitio sigue funcionando: la búsqueda usa su propio buscador
por palabras clave y el cuadro "Resultado del modelo" muestra el mensaje de respaldo
en vez de confianza/sentimiento.

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
