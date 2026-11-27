# Instrucciones para quien maneja n8n

**Tarea (prioridad P1, requerimientos RA-34 y RA-15, brecha B1):** el Cerebro
solo debe usar la respuesta de la API cuando se sabe que **no** es texto
generado por una IA.

**Por qué:** hoy acepta cualquier respuesta con confianza de 0,65 o más. Si la
API tiene un conector LLM o respuestas en cola, puede enviar un texto generado
como si fuera del FAQ, sin aviso. La regla R10 lo prohíbe. Esto se dedujo del
código y del flujo exportado; no se ha reproducido.

El portal y la API los trabaja otra persona (RA-31). **Los dos cambios son
independientes**: no tienes que esperar el suyo, y no tienes que tocar
`dist/` ni `model/`.

Referencias: [`CONSTITUTION.md`](../CONSTITUTION.md) (R1, R8, R10, R11),
[`FLUJOS.md`](../FLUJOS.md) (significado de `capa` y brechas) y
[`REQUERIMIENTOS_ABIERTOS.md`](../REQUERIMIENTOS_ABIERTOS.md).

## Paso 0. Revisa qué está expuesto (hazlo primero, RA-21)

Según los flujos exportados en el repositorio, ninguna de las tres puertas
cumple R11: una superficie que responde no puede quedar al alcance de quien no
esté controlado.

- **Puerta Web:** es pública. *Allowed Origins* y `?chat=demo` no controlan el
  acceso.
- **Puertas de WhatsApp (Evolution y Emulador):** el secreto o la firma
  verifican a la plataforma, no a quien escribe. No filtran remitentes.

Anota qué flujos están activos en el servidor, desde dónde se alcanzan, a qué
número está conectada cada puerta y si usan documentos reales. **Si una puerta
con documentos reales está abierta a cualquiera, avisa al equipo de inmediato y
acuerden desactivarla.** Una lista de teléfonos permitidos no es suficiente:
identificar un número no es controlar el acceso (R7).

El cambio de abajo **no** resuelve este punto.

## Paso 1. Comprueba antes de cambiar

1. **La API devuelve `capa`.** En n8n, ejecuta de prueba el nodo *Preguntar al
   modelo FAQ* con una pregunta del FAQ y mira su salida.
   - Si no aparece `capa`, la API desplegada es anterior. Puedes aplicar el
     cambio igual: todo pasará al Nivel 2. Sigue siendo correcto, pero más
     lento. Avisa a quien mantiene la API.
2. **No hay conector ni cola.** Mientras este cambio no esté aplicado, deben
   estar así. Con el nombre de contenedor del README (`prebel-rrhh-api`):

   ```bash
   docker exec prebel-rrhh-api printenv LLM_CONECTOR
   docker exec prebel-rrhh-api sh -c 'cat "${RETROALIMENTACION_DIR:-/app/model}/retroalimentacion.json" 2>/dev/null || echo "sin cola"'
   ```

   Lo esperado: el primer comando no imprime nada, y el segundo muestra
   `sin cola` o `[]`. La cola puede contener preguntas de personas: no la copies
   al repositorio ni a un chat. Si no está vacía o hay conector, avisa al
   equipo.
3. **Tu flujo coincide con el del repositorio.** Confirma que el nodo *Embedding
   de la pregunta* lee `$('Recibir pregunta').first().json.pregunta`.
4. **Guarda una copia** del flujo actual del servidor (menú *Download*), fuera
   del repositorio: puede tener datos reales.

## Paso 2. Haz el cambio

En el Cerebro (`03-cerebro-ia`), abre el nodo **¿Hay respuesta segura del
FAQ?**. Ya tiene una condición (`confianza` mayor o igual a 0,65). **No la
quites.** Agrega una segunda:

| Campo | Valor |
|---|---|
| Valor | `{{ ['predictivo','ml'].includes($json.capa) }}` |
| Operador | Boolean → *is true* |
| Combinación | **AND** |

No cambies las salidas: la verdadera sigue yendo a *Responder con FAQ* y la
falsa a *Embedding de la pregunta* (Nivel 2, que ya avisa que responde una IA).

**Usa esa lista de valores permitidos.** No la sustituyas por "distinto de
`llm`": dejaría pasar como FAQ cualquier valor nuevo o una respuesta sin
`capa`. No necesitas usar `tipo`.

Qué debe hacer el Cerebro con cada valor (lo que significa cada uno está en
[`FLUJOS.md`](../FLUJOS.md), "Qué significa `capa`"):

| `capa` | El Cerebro |
|---|---|
| `predictivo`, `ml` | La usa si además `confianza` ≥ 0,65 |
| `llm`, `retroalimentacion` (texto generado) | La descarta y sigue al Nivel 2 |
| ausente, `null` u otro valor | La descarta y sigue al Nivel 2 |

Las puertas no cambian.

## Paso 3. Prueba cada caso

Alcanza con un n8n local (ver "Probar los flujos en un n8n local" en
[`README.md`](README.md)). Usa solo datos ficticios.

1. En *Recibir pregunta*, fija (*pin data*) la entrada:
   `[{"pregunta": "¿Cómo solicito vacaciones?"}]`.
2. En *Preguntar al modelo FAQ*, fija la salida de cada caso, por ejemplo:
   `[{"reply": "Texto de prueba", "confianza": 0.70, "capa": "llm"}]`.
3. Ejecuta y mira por qué salida sale *¿Hay respuesta segura del FAQ?*.

| # | `capa` | `confianza` | Debe ir a |
|---|---|---|---|
| 1 | `predictivo` | 0.98 | Responder con FAQ |
| 2 | `ml` | 0.80 | Responder con FAQ |
| 3 | `llm` | 0.70 | Nivel 2 |
| 4 | `retroalimentacion` | 0.70 | Nivel 2 |
| 5 | (sin el campo) | 0.90 | Nivel 2 |
| 6 | `null` | 0.90 | Nivel 2 |
| 7 | `otro-valor` | 0.90 | Nivel 2 |
| 8 | `ml` | 0.50 | Nivel 2 |

4. **Caso 9, la API no responde:** quita el dato fijado, apunta la URL del nodo
   a un servidor que no exista y ejecuta. Debe llegar a *Embedding de la
   pregunta* (RA-27). Restaura la URL.

En un n8n local sin Ollama ni la tabla de fichas, el Nivel 2 terminará en error
o en la disculpa. Es esperado: lo que se prueba es **por qué salida** va el
flujo.

Antes de terminar, **quita todos los datos fijados** y revisa que la URL sea la
original.

## Paso 4. Aplica en el servidor

1. Haz el mismo cambio en el servidor (o importa el flujo probado y vuelve a
   ajustar tabla, credenciales y marcadores, como indica el README).
2. Prueba una pregunta del FAQ, que debe responder el Nivel 1, y una fuera del
   FAQ, que debe ir al Nivel 2.
3. Si algo falla, restaura la copia del paso 1. Con esa copia vuelve la brecha:
   mantén la API sin conector y con la cola vacía.

## Paso 5. Actualiza el repositorio

**Aplica además estas dos correcciones de texto en el servidor antes de
exportar.** Ya están en el repositorio; si no las haces en el servidor, la
exportación las deshace.

- Cerebro, notas del nodo *Preguntar al modelo FAQ*: el final debe decir
  `caída controlada de R8 en CONSTITUTION.md.` (la versión anterior citaba la
  regla del portal estático, que no trata esto).
- Puerta Web, nota del flujo: copia el texto de
  `workflows/04-puerta-web.json` del repositorio. El script no exporta esta
  puerta, así que impórtala o edítala a mano.

Actualiza también la nota *Nota: qué es este flujo* del Cerebro: el Nivel 1
responde si la confianza alcanza el umbral **y** `capa` es `predictivo` o `ml`.

Luego exporta con `scripts/exportar_flujos.py`, como explica su encabezado. Ese
script **sobrescribe los flujos 01 a 03** del repositorio con los del servidor.

- Revisa el diff completo: no debe revertir cambios que no hiciste a propósito.
- **Nunca subas `*.real.json` ni `data/`.** Busca en el diff teléfonos, correos
  y nombres reales (R1).

En el mismo PR:

| Archivo | Cambio |
|---|---|
| `n8n/README.md`, "Cómo responde el cerebro" | Agregar la condición de `capa` al Nivel 1 |
| `FLUJOS.md` §3 | Actualizar el texto y el diagrama; en §4, quitar la fila B1 y ajustar la frase que menciona B1 a B6 |
| `REQUERIMIENTOS_ABIERTOS.md` | Quitar RA-15 de brechas y RA-34 de la sección 5 (incluido el orden de trabajo); pasarlos a **Cerrados** con la evidencia; ajustar RA-22 |
| Este documento | Al cerrar la tarea, eliminarlo junto con el aviso que lo enlaza en `n8n/README.md`; lo que siga pendiente ya está en los requerimientos abiertos |

Luego, desde la raíz del repositorio:

```bash
pip install -r requirements-dev.txt
pytest tests/test_documentacion.py -v
```

Córrelas en un clon con git. En una copia sin `.git` algunas se saltan, y un
salto no cuenta como verde.

Si falla la prueba de trazabilidad, **no edites `tests/trazabilidad.json` para
silenciarla**. Te indica qué reglas revisar: sigue el procedimiento de R0 y
actualiza el registro solo después. Antes de abrir el PR, las tres suites deben
estar en verde (R12; ver "Tests" en el [`README.md`](../README.md) principal).

## Listo cuando

- [ ] Está anotado y comunicado qué puertas están activas y quién las alcanza.
- [ ] Los casos 1 a 9 dan el resultado esperado, y la evidencia está en el PR.
- [ ] El cambio está en el servidor y sin datos fijados.
- [ ] El repositorio coincide con el servidor, sin datos reales.
- [ ] La documentación está actualizada y las pruebas en verde.

El PR debe decir qué se probó en un n8n local y qué en el servidor.

## Qué no incluye esta tarea

- **`solo_local`:** es una propuesta para que la API responda sin usar el
  conector ni la cola. El equipo aún no la aprueba y la API no la admite. No la
  agregues todavía.
- **Control de acceso de las puertas (RA-18 y RA-19):** falta que el equipo
  elija el mecanismo (RA-09).
- **El ciclo API → n8n → API (B3):** este cambio no lo evita. No uses el Cerebro
  como backend del conector de la API mientras siga llamándola (R10).
