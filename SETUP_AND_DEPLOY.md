# Configuración y despliegue

Mapa de **todos** los componentes de la solución, sus requisitos mínimos en
conjunto (herramientas y cuentas), y a qué documento ir para el detalle de
cada uno. Este documento no repite el "cómo" de cada pieza -- eso vive en
`README.md`, `MODEL_TRAINING.md`, `MODEL_TUNING.md` y `n8n/README.md`, cada
uno con su propio alcance. Este es el punto de entrada para ver el conjunto
completo antes de ponerse a trabajar. Para **qué camino toma cada
pregunta** (no el despliegue, sino el flujo en tiempo de ejecución), ver
[`FLUJOS.md`](FLUJOS.md).

## 1. Mapa de componentes

| Componente | Qué es | Dónde corre | Documentación |
|---|---|---|---|
| Portal estático | `dist/`: HTML/CSS/JS, perfil, trámites, búsqueda por palabras clave | GitHub Pages (público) o cualquier servidor estático local | `README.md` |
| Capa semántica + orquestador | `model/rrhh_api.py` + `model/rrhh_bot.py` (elige una respuesta del FAQ ficticio) + `model/orquestador.py` (decide predictivo/ML/LLM, 95%/75%) | PC del operador (`127.0.0.1`), o monolito contenerizado (`docker-compose.yml`) | `README.md`, `FLUJOS.md`, `MODEL_TRAINING.md` |
| Conector LLM (opcional) | `model/conectores.py`: vía MCP, apagado por defecto (`LLM_CONECTOR` sin definir) | Mismo proceso que la capa semántica | `FLUJOS.md` |
| Reuso por retroalimentación | `model/rag_retroalimentacion.py`: reusa respuestas del LLM para preguntas parecidas, por similitud (umbral 85%) | Mismo proceso; `retroalimentacion.json` persiste en el volumen de `docker-compose.yml` | `FLUJOS.md` |
| Entrenamiento/calibración | `model/entrenar.py`: cachea embeddings, calibra el umbral, sugiere variancia nueva | PC del operador (o durante el build del `Dockerfile`) | `MODEL_TRAINING.md` |
| Exploración de variancia | Modelos de paráfrasis locales probados para `--augmentar` | PC del operador (exploración puntual, documentada) | `MODEL_TUNING.md` |
| Canal WhatsApp local | `model/whatsapp_service.py`: puente a un entorno compatible con WhatsApp Cloud API | PC del operador + emulador local (`whatsapp-emulator/`, fuera de este repo) | `README.md` (sección "Canal de WhatsApp") |
| Canal n8n (WhatsApp real + burbuja web) | `n8n/`: Cerebro (RAG+Ollama, Tier 2 Agentic) + 3 puertas | Servidor del equipo (real) **o** n8n local vía Docker (pruebas) | `n8n/README.md` |
| Contenedor Tier 1 para n8n | Empaqueta `model/rrhh_api.py` para que el Cerebro lo alcance | Misma red privada de Docker que n8n/Ollama (real), o red Docker local (pruebas) | `Dockerfile`, `n8n/README.md` |
| Gestión del repositorio | Ramas, PRs, revisiones | GitHub (`hdvergara/prebel-conecta`, público) | este documento, §3 |

## 2. Requisitos mínimos (todos los componentes)

| Herramienta / cuenta | Mínimo | Para qué componente(s) | Notas |
|---|---|---|---|
| Python | 3.10+ | Capa semántica, entrenamiento, unit tests de Python | Probado con 3.11 (dentro del `Dockerfile`) y 3.15 (local) |
| Node.js | 18+ | Unit tests de JS, E2E con Playwright | No hace falta para correr el portal ni la API |
| Git | cualquier versión reciente | Clonar y versionar | `prebel-conecta/` es su propio repositorio |
| PowerShell | incluido en Windows, o 7+ multiplataforma | `iniciar-conecta.ps1` | |
| Cuenta de GitHub con acceso de colaborador a `hdvergara/prebel-conecta` | -- | Hacer push de ramas, abrir PRs | Pídelo a quien administre el repositorio; sin esto se puede trabajar en un fork |
| `gh` CLI autenticado (`gh auth login`, scope `repo`) | 2.x | Crear/gestionar PRs desde la terminal | Opcional -- la interfaz web de GitHub cubre lo mismo; probado con 2.105 |
| Docker Desktop o Docker Engine | reciente | Monolito (`docker-compose.yml`), `Dockerfile` (Tier 1 de n8n), pruebas locales de n8n (§4) | Probado con Docker Desktop 29.9, incluido `docker compose up --build`. **No** hace falta para correr el portal, la API o los tests -- son componentes aparte |
| Cuenta de Docker Hub | opcional | Descargar `python:3.11-slim`, `n8nio/n8n` | Las descargas anónimas alcanzan para este proyecto; una cuenta gratuita solo ayuda si se topa el límite de descargas anónimas |
| Cuenta de Hugging Face (`HF_TOKEN`) | opcional | Descargar los modelos preentrenados sin límite de descargas anónimas | Sin token, las descargas funcionan igual pero con límites más bajos (se ve como aviso al construir el `Dockerfile`) |
| Acceso al servidor n8n del equipo (Coolify) | -- | Canal n8n **real** (§4), WhatsApp real vía Evolution | Acceso administrado por el equipo -- pídelo a quien gestione ese servidor; no es autoservicio |
| Ollama con `embeddinggemma` y el modelo de redacción (hoy `gemma4:e2b`) | -- | Tier 2 (Agentic) del canal n8n | Ya instalado en el servidor del equipo; si montas tu propio n8n real, instálalo tú (ver `n8n/README.md`) |
| Cuenta/instancia de Evolution API | -- | Puerta Evolution (WhatsApp real) | Gestionada por el equipo |
| Navegador | cualquiera reciente | Abrir la demo | Playwright instala su propio Chromium para los e2e; no usa el del sistema |

Nada de lo anterior requiere GPU ni build tools de C/C++.

## 3. Provisión de cuentas y accesos

- **GitHub:** pide acceso de colaborador a quien administre
  `hdvergara/prebel-conecta`. Sin ese acceso, el flujo normal es forkear el
  repositorio y abrir el PR desde el fork.
- **`gh` CLI:** `gh auth login --hostname github.com --git-protocol https
  --web` (flujo de dispositivo, pide completar un código en el navegador).
  Solo hace falta si vas a crear PRs desde la terminal; usar la web de
  GitHub no requiere esto.
- **Servidor n8n / Evolution API del equipo:** administrado por el equipo,
  no es autoservicio -- pide acceso a quien lo gestione. Para trabajar sin
  ese acceso (p. ej. para validar la lógica de un flujo antes de pedir que
  lo importen), usa n8n local con Docker (§4 y la sección "Probar los
  flujos en un n8n local" de `n8n/README.md`).
- **Docker Hub / Hugging Face:** ambas cuentas son opcionales para este
  proyecto -- las descargas anónimas alcanzan; solo ayudan si se topa un
  límite de tasa.

## 4. Nota técnica: n8n local vs. n8n real para pruebas

El canal n8n se puede probar de dos formas válidas, **a discreción de quien
desarrolla o de SDET**, según qué se esté verificando:

- **n8n local (Docker, imagen oficial `n8nio/n8n`:
  <https://hub.docker.com/r/n8nio/n8n>):** rápido, no depende del servidor
  del equipo, no necesita credenciales del equipo. Sirve para validar la
  **lógica y el cableado** de un cambio a un flujo -- que el JSON importe
  sin errores, que las conexiones entre nodos sean las esperadas, que el
  Tier 1 responda directo cuando hay confianza y caiga con gracia al Tier 2
  si no la hay o si falla. **No** valida la calidad real del RAG (Ollama,
  documentos reales) ni la entrega real de WhatsApp/Evolution, porque esas
  piezas no existen en una instancia local recién creada.
- **n8n real (servidor del equipo):** la única forma de validar el stack
  completo -- Ollama real, la Data Table `prebel_kb` con los documentos
  reales, entrega real por WhatsApp/Evolution o por el emulador del
  servidor. Necesaria antes de dar por "listo" cualquier cambio que toque
  el contenido o la calidad del Tier 2, o las puertas de WhatsApp mismas.

Ninguna reemplaza a la otra; se complementan. El procedimiento paso a paso
para montar la instancia local (crear la red de Docker, importar los
flujos por CLI, credencial placeholder de Ollama, probar contra el webhook
del *Chat Trigger*, limpieza) está en la sección "Probar los flujos en un
n8n local" de [`n8n/README.md`](n8n/README.md).

## 5. Por dónde empezar, según lo que vayas a tocar

| Vas a... | Empieza en |
|---|---|
| Entender qué camino toma una pregunta según el canal | `FLUJOS.md` |
| Correr el portal y la API localmente | `README.md` → Setup, Run |
| Tocar `model/faq_rrhh.json` o recalibrar el modelo | `MODEL_TRAINING.md` |
| Evaluar variancia/paráfrasis para el FAQ | `MODEL_TUNING.md` |
| Probar el canal de WhatsApp local (emulador) | `README.md` → "Canal de WhatsApp" |
| Cambiar un flujo de n8n (Cerebro o una puerta) | `n8n/README.md`, valida primero con n8n local (§4) |
| Desplegar el contenedor del Tier 1 en el servidor del equipo | `Dockerfile`, `n8n/README.md` → "Cómo montarlo en otro n8n" |
| Abrir un PR | este documento §3, `CONSTITUTION.md` → harness (qué debe quedar en verde antes) |
