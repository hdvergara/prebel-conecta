# Requerimientos abiertos

Todo punto de esta lista **se trata como un requerimiento abierto**: no está
confirmado, decidido, implementado o verificado, y no debe presentarse como
resuelto.

- Esta lista no crea reglas ni autoriza nada. Las reglas están en
  [`CONSTITUTION.md`](CONSTITUTION.md); el detalle de las brechas, en
  [`FLUJOS.md`](FLUJOS.md) §4.
- Un punto se cierra con una decisión registrada en
  [`DECISIONES.md`](DECISIONES.md) o con evidencia (prueba o verificación
  descrita en el PR). No se borra: pasa a **Cerrado**, con su referencia.
- Si cerrarlo cambia una regla, se aplica R0.
- Estado de todos los puntos listados abajo: **Abierto**.

## 1. Por confirmar

Texto ya redactado en las reglas que el equipo no ha confirmado. Figurar aquí no
suspende ninguna regla: si algo queda en espera, lo dice la propia regla.

| ID | Requerimiento | Referencia | Se cierra cuando |
|---|---|---|---|
| RA-02 | Confirmar que un valor ficticio en el FAQ se permite si la respuesta dice que es un ejemplo. R5 deja el permiso en espera hasta confirmarlo | R5, D5 | El equipo lo aprueba o lo rechaza |
| RA-03 | Confirmar la obligación de no presentar texto generado como respuesta del FAQ (agregada al redactar la regla) | R10, D6 | El equipo la aprueba o la corrige |
| RA-04 | Confirmar el alcance de toda superficie de respuesta, incluida su consecuencia: las puertas de WhatsApp necesitan verificar a la persona, y una lista de teléfonos no basta | R7, R11, D10 | El equipo acepta la consecuencia o enmienda la regla |
| RA-05 | Confirmar que la presunción agnóstica decide quién alcanza una superficie, no lo que esta puede hacer en condiciones controladas (acotación agregada al redactar) | CONSTITUTION §0, D10 | El equipo la aprueba o la corrige |
| RA-06 | Confirmar que el acceso entre orígenes no admite credenciales (condición agregada a la excepción MVP) | R11, D13 | Se confirma, o se enmienda si un ambiente autentica con cookies o autenticación básica |
| RA-37 | Confirmar cómo pesa la jerarquía normativa: usa las clases de precedencia (protección de datos, disponibilidad, comportamiento), no cuál regla originó la cadena; con peso igual no se ejecuta lo que niega la premisa | R0, D14 | El equipo lo aprueba o define otro criterio para la regla fundacional |
| RA-40 | Confirmar que una comprobación saltada por falta de git no cuenta como verde (condición agregada al resolver la revisión del PR) | R12, D15 | El equipo la aprueba o la corrige |

## 2. Por decidir

| ID | Requerimiento | Referencia | Se cierra cuando |
|---|---|---|---|
| RA-07 | Habilitar o no CORS en el contenedor. Hoy está apagado y una prueba lo exige; la excepción MVP permite abrirlo | R11, FLUJOS §4 | Se decide según exista o no un portal en otro origen que lo llame |
| RA-08 | Definir los ambientes y cómo se cruzan. De esto depende el fin de la excepción MVP | R11, D13 | Los ambientes quedan registrados como decisión |
| RA-09 | Elegir el control de acceso de las superficies: puertas de WhatsApp, puerta Web y cualquier proxy | R7, R11 | Hay un mecanismo decidido que verifica a quien pregunta |
| RA-10 | Definir cómo funciona la demo publicada: un proxy como `/api/reply` exige control de acceso en la página y en la ruta; sin él, el recuadro queda sin backend | R2, R3, R11 | Se elige una de las dos vías |
| RA-11 | Decidir si la política de orígenes de la puerta Web de n8n entra en la excepción MVP, que hoy cubre solo la API. No sustituye al control de acceso | R11 | Se amplía la excepción o se confirma que no |
| RA-13 | Completar los marcadores del FAQ (13 de 15 entradas). Depende de RA-02; los valores reales no pueden entrar al repositorio | R1, R5 | Se completan o se decide dejarlos |
| RA-14 | Decidir si los detectores de saludo siguen separados (hay tres) | FLUJOS §4 | Se registra la decisión |
| RA-38 | Decidir si el bloqueo por jerarquía se implementa en el código. El ejemplo formal lo describe automático; hoy no hay ningún mecanismo y se aplica al revisar | R0, D14 | Se implementa y se prueba, o se decide que es un control de revisión |
| RA-42 | Decidir si las dos entradas del FAQ sin marcadores (crédito de vivienda y retiro de cesantías) también deben ir al Nivel 2 del Cerebro, que tiene las condiciones reales | D16, FLUJOS §4 | Se decide y se prueba a dónde cae cada pregunta |
| RA-41 | Decidir la propuesta `solo_local`: que la API pueda responder sin usar el conector ni la cola (por ejemplo, para el Cerebro de n8n). Hoy la API no la admite | R10 | Se aprueba e implementa con pruebas, o se descarta |

## 3. Brechas: el código no cumple una regla

El detalle y las condiciones de cada una están en [`FLUJOS.md`](FLUJOS.md) §4.

| ID | Brecha | Resumen | Se cierra cuando |
|---|---|---|---|
| RA-16 | B2 | Nada en el código impide abrir la API a llamadas no controladas | Existe un control o una verificación de despliegue |
| RA-17 | B3 | Nada impide el ciclo API → n8n → API | Existe una entrada de backend que no llama a la API, o un control |
| RA-18 | B4 | La puerta Web no tiene control de acceso | Cumple R11 |
| RA-19 | B5 | Las puertas de WhatsApp no verifican a quien escribe | Cumplen R11 |
| RA-20 | B6 | El puente local escucha en toda la red con un secreto público por defecto | Cumple R11 |
| RA-39 | B8 | El portal puede mostrar texto generado sin distinguirlo del FAQ | El portal mira `capa` y avisa o descarta, con una prueba |

## 4. Sin verificar

| ID | Requerimiento | Se cierra cuando |
|---|---|---|
| RA-22 | Ejecutar las brechas B2 a B6 y B8, hoy deducidas del código y de los workflows exportados (B1 se cerró con RA-15) | Cada una se reproduce o se descarta |
| RA-23 | Comprobar que los temas que el Nivel 1 responde están en los documentos reales (lo reporta el equipo) | Se compara con las fichas, sin copiarlas al repositorio |
| RA-24 | Medir la latencia del Nivel 2: se reportaron 6–9 s y el repositorio documenta 20–26 s | Hay una medición con sus condiciones (modelo cargado o en frío) |
| RA-25 | Repetir en el servidor las confianzas medidas solo con el modelo local | Hay resultados del servidor |
| RA-26 | Probar el conector contra un servidor MCP real; no existe uno montado | Hay una prueba de integración |
| RA-27 | Probar en n8n la rama de error del Nivel 1 y que el flujo llegue al Nivel 2 | Hay una ejecución registrada |
| RA-28 | Probar la burbuja `@n8n/chat` contra un Chat Trigger real | Hay una ejecución en condiciones controladas |
| RA-29 | Comprobar si el navegador bloquea las llamadas de otra página a la API local | Se prueba en los navegadores de la demo |

## 5. Funcionalidad pendiente

Prioridad **propuesta**, pendiente de que el equipo la confirme. Criterios, en
orden: cumplir una regla; ser requisito de otro punto; cuándo empieza el daño.
Ordena **solo esta sección**: no antecede a las brechas de acceso
(R11, RA-16 y RA-18 a RA-20).

- **P1:** necesario antes de configurar un conector o de usar una cola con datos.
- **P2:** requisito para que escalar funcione en el portal.
- **P3:** funcionalidad que depende de lo anterior.
- **P4:** puede esperar; no bloquea nada de esta lista.

| ID | Prioridad | Requerimiento | Referencia | Depende de | Por qué ahí |
|---|---|---|---|---|---|
| RA-31 | P1 | El portal no muestra `capa`, `tipo` ni `guia`, así que no explica por qué respondió así | R10, FLUJOS §2 | -- | Su parte urgente, avisar del texto generado, cierra RA-39. Explicar el porqué y mostrar `guia` es P3 |
| RA-32 | P2 | Si la API tarda más que la espera del portal, se pierde también la respuesta ML ya calculada | R2, R8 | -- | Hoy casi no se nota; aparece al conectar un modelo lento |
| RA-30 | P3 | El portal no ofrece "seguir buscando": nunca envía `seguir` | R8 | RA-31, RA-32, RA-26 | Sin conector ni cola, el botón devolvería la misma respuesta; con un modelo lento, el portal la perdería |
| RA-33 | P3 | WhatsApp local no pasa por el orquestador | FLUJOS §4 | Decidirlo; RA-34 (cerrado) como referencia del aviso | Al unificarlo, ese canal puede recibir texto generado: necesita el aviso (R10) y revisar cómo personaliza con datos (R7) |
| RA-35 | P4 | Llevar una respuesta de la cola al FAQ es manual: solo se puede listar | R5, D4 | RA-02, RA-26 | La revisión manual es la decisión vigente; facilitarla exige además cumplir R1 |
| RA-36 | P4 | `n8n/scripts/exportar_flujos.py` no exporta la puerta Web, que aún no tiene identificador en el servidor | -- | RA-18 | La puerta no puede activarse mientras no cumpla R11 |

Orden de trabajo propuesto: RA-31 (aviso) → RA-32 → RA-30 → RA-33 →
RA-35 y RA-36.

Cada punto de esta sección se cierra cuando está implementado y probado, o
cuando se decide no hacerlo.

## Cerrados

| ID | Requerimiento | Cierre |
|---|---|---|
| RA-01 | Redacción de la salvaguarda de transitividad, con su definición y su procedimiento | Aprobada por el equipo, con ejemplo formal ([`DECISIONES.md`](DECISIONES.md), D14) |
| RA-15 | B1: n8n podía enviar texto generado sin aviso de IA | 2026-11-27. El nodo *¿Hay respuesta segura del FAQ?* del Cerebro exige además `capa` en `['predictivo','ml']` (lista de valores permitidos); lo demás sigue al Nivel 2, que avisa. Evidencia en el PR: casos 1–9 de la tarea y dos preguntas reales en el servidor |
| RA-34 | El Cerebro de n8n no usaba `tipo` ni `capa` de la API | 2026-11-27, junto con RA-15: usa `capa`; `tipo` no hace falta para esta regla |
| RA-21 | Comprobar qué está activo en el servidor del equipo y quién lo alcanza | 2026-11-27. La puerta Web y la de Evolution estaban activas, sin control de acceso y conectadas a documentos reales: se apagaron ese día. Las ejecuciones guardadas (desde el 2026-11-23) solo muestran personas del equipo; las anteriores ya no existen. La puerta Emulador sigue activa detrás del inicio de sesión del emulador (B5 sigue abierta). También se quitó un proxy `/api/reply` del portal del servidor (RA-10, RA-16). La demo se muestra desde una sesión de n8n |
| RA-12 | Resolver que el FAQ ficticio tape temas del RAG de n8n | 2026-11-27, con D16: el Cerebro descarta las respuestas del Nivel 1 que traen marcadores `[…]`. Evidencia en el PR: las 15 preguntas del FAQ contra la API del servidor (13 van al Nivel 2, vivienda y cesantías se quedan en el Nivel 1) y pruebas reales en el Cerebro. Lo que queda abierto pasa a RA-42 |
