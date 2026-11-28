# Instrumentos para asistentes

Sirven igual con cualquier asistente. La fuente es
[`AGENTS.md`](../../AGENTS.md); cada herramienta solo necesita llegar a ella.

| Herramienta | Cómo llega a `AGENTS.md` | Archivo propio |
|---|---|---|
| Codex | Lo lee del repositorio. Su límite predeterminado es de 32 KiB | Ninguno |
| Google Antigravity ("Gravity") | Según su documentación, lo lee como regla del espacio de trabajo | Ninguno |
| Claude Code | [`CLAUDE.md`](../../CLAUDE.md) lo importa | Una línea |
| ChatGPT | No se da por hecho que lea el repositorio: se pega [`chatgpt.md`](chatgpt.md) y se adjuntan los archivos | Texto para pegar |

La carga en cada herramienta **no se ha probado** (RA-47). Para comprobarla,
pregunta al asistente: "¿Qué regla dice qué archivos no puedes abrir y qué
debes leer primero?". Debe responder R15 y la constitución.

No crees `GEMINI.md`, `.agents/rules/` ni otros archivos de instrucciones con
contenido propio: dos fuentes acaban distintas (R13). Si una herramienta exige
el suyo, que solo apunte a `AGENTS.md`.

## Cómo usar un instrumento

Pide, en cualquier herramienta: *"Sigue
`especificaciones/instrumentos/especificar.md` para RA-NN"*. Cada uno define su
entrada, sus pasos, lo que entrega y cuándo detenerse.

| Instrumento | Entrega |
|---|---|
| [`especificar.md`](especificar.md) | Especificación del cambio, sin código |
| [`transitividad.md`](transitividad.md) | Cadenas revisadas y conflictos |
| [`implementar.md`](implementar.md) | Pruebas, código y documentación |
| [`revisar.md`](revisar.md) | Hallazgos verificados, sin modificar nada |
