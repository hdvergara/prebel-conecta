# Tareas

Plan de trabajo derivado de
[`REQUERIMIENTOS_ABIERTOS.md`](../REQUERIMIENTOS_ABIERTOS.md). Cada
requerimiento abierto está en **exactamente una** tarea
(`tests/test_tareas.py` lo comprueba).

- El requerimiento dice **qué** falta y **cuándo se cierra**; aquí no se repite.
  La tarea dice quién lo mueve, en qué orden y por dónde empezar.
- Una tarea no crea requerimientos ni autoriza nada: un asistente sigue
  necesitando que le pidan lo que indica R15.
- **Responsables, orden y olas son una propuesta** que el equipo puede cambiar.
- **Lista:** no depende de otra tarea. **Bloqueada:** espera las que indica.
  "Lista" no significa aprobada.
- Si cambia el comportamiento, la especificación va antes del código o en el
  mismo PR, con la excepción que da R14. Usa los
  [instrumentos](instrumentos/README.md).
- Ninguna ola ni dependencia de este plan pide esperar para reducir exposición,
  como apagar una puerta.
- Al cerrar un requerimiento se quita de su tarea; la tarea que queda sin
  ninguno se borra y se actualizan las que dependían de ella.

## Ola 0. Exposición y acceso (lo de protección de datos va primero)

| ID | Tarea | Requerimientos | Responsable | Depende de | Estado |
|---|---|---|---|---|---|
| TAR-01 | Poner el puente local de WhatsApp en condiciones controladas | RA-20 | Cualquier colaborador | -- | Lista |
| TAR-02 | Elegir cómo funciona la demo publicada e impedir que la API se abra por descuido | RA-10, RA-16 | Portal y API, Equipo | -- | Lista |
| TAR-03 | Impedir el ciclo entre la API y n8n | RA-17 | Portal y API, n8n | -- | Lista |
| TAR-04 | Confirmar el alcance de las superficies y de la presunción sobre datos | RA-04, RA-05 | Equipo | -- | Lista |
| TAR-05 | Elegir el control de acceso y la política de la puerta Web | RA-09, RA-11 | Equipo, n8n | TAR-04 | Bloqueada |
| TAR-06 | Aplicar el control de acceso en la puerta Web | RA-18 | n8n | TAR-05 | Bloqueada |
| TAR-30 | Verificar a quien escribe en las puertas de WhatsApp de n8n | RA-19 | n8n | TAR-05 | Bloqueada |
| TAR-33 | Decidir cuánto se conserva lo que escriben las personas | RA-51 | Equipo, n8n, Portal y API | -- | Lista |
| TAR-35 | Orientar sin recibir datos personales y decidir la invitación del puente local | RA-54, RA-55 | Equipo, n8n, Portal y API | -- | Lista |

## Ola 1. Confirmaciones y decisiones de reglas

| ID | Tarea | Requerimientos | Responsable | Depende de | Estado |
|---|---|---|---|---|---|
| TAR-07 | Confirmar el peso de la jerarquía normativa y si el bloqueo se programa | RA-37, RA-38 | Equipo | -- | Lista |
| TAR-08 | Confirmar las condiciones de verificación y de especificación primero | RA-40, RA-43 | Equipo | -- | Lista |
| TAR-09 | Confirmar la regla para asistentes de IA | RA-46 | Equipo | -- | Lista |
| TAR-10 | Confirmar el aviso de texto generado y el acceso sin credenciales entre orígenes | RA-03, RA-06 | Equipo | -- | Lista |
| TAR-11 | Decidir si el FAQ admite valores ficticios | RA-02 | Equipo | -- | Lista |
| TAR-31 | Completar los marcadores del FAQ o dejarlos | RA-13 | Equipo | TAR-11 | Bloqueada |
| TAR-36 | Confirmar la clasificación de las reglas frente a las respuestas de Prebel | RA-53 | Equipo | -- | Lista |

## Ola 2. Respuestas honestas

| ID | Tarea | Requerimientos | Responsable | Depende de | Estado |
|---|---|---|---|---|---|
| TAR-12 | Avisar del texto generado (o descartarlo) y explicar la respuesta en el portal | RA-31, RA-39 | Portal y API | -- | Lista |
| TAR-34 | Decidir en qué fuentes se fundamenta el texto generado | RA-52 | Equipo | -- | Lista |
| TAR-13 | Decidir si la API admite responder sin conector ni cola | RA-41 | Equipo, n8n, Portal y API | -- | Lista |
| TAR-14 | Conservar la respuesta local cuando escalar tarda | RA-32 | Portal y API | -- | Lista |
| TAR-18 | Probar el conector contra un servidor MCP real | RA-26 | Portal y API | -- | Lista |
| TAR-15 | Ofrecer "seguir buscando" | RA-30 | Portal y API | TAR-12, TAR-14, TAR-18 | Bloqueada |

## Ola 3. Verificación

| ID | Tarea | Requerimientos | Responsable | Depende de | Estado |
|---|---|---|---|---|---|
| TAR-16 | Reproducir B2 a B6 y B8 en condiciones controladas | RA-22 | Portal y API, n8n | -- | Lista |
| TAR-17 | Probar la rama de error en el Cerebro real | RA-27 | n8n | -- | Lista |
| TAR-19 | Medir en el servidor latencia, confianzas y cobertura de temas | RA-23, RA-24, RA-25 | n8n | -- | Lista |
| TAR-20 | Probar la burbuja de chat en condiciones controladas | RA-28 | n8n | -- | Lista |
| TAR-21 | Comprobar si el navegador bloquea llamadas de otra página a la API local | RA-29 | Portal y API | -- | Lista |
| TAR-22 | Probar la carga de instrucciones en cada asistente y decidir si R15 se refuerza | RA-47, RA-48 | Equipo | -- | Lista |
| TAR-23 | Hacer que las pruebas no dependan del entorno de quien las corre | RA-50 | Portal y API | -- | Lista |
| TAR-37 | Medir la precisión con preguntas construidas desde los documentos | RA-60 | n8n | -- | Lista |

## Ola 4. Estructura y evolución

| ID | Tarea | Requerimientos | Responsable | Depende de | Estado |
|---|---|---|---|---|---|
| TAR-24 | Definir los ambientes y decidir CORS en el contenedor | RA-07, RA-08 | Equipo | -- | Lista |
| TAR-25 | Decidir si WhatsApp local pasa por el orquestador | RA-33 | Equipo, Portal y API | -- | Lista |
| TAR-32 | Decidir si los detectores de saludo siguen separados | RA-14 | Equipo | -- | Lista |
| TAR-26 | Resolver o aceptar la dependencia circular entre contextos | RA-44 | Portal y API | -- | Lista |
| TAR-27 | Decidir el alcance del autoservicio y de los archivos del portal que no se cargan | RA-45, RA-49 | Equipo | -- | Lista |
| TAR-28 | Facilitar el paso de la cola al FAQ | RA-35 | Portal y API | TAR-11, TAR-18 | Bloqueada |
| TAR-29 | Exportar la puerta Web desde el servidor | RA-36 | n8n | TAR-06 | Bloqueada |
| TAR-38 | Preguntar el público del colaborador cuando cambie la respuesta | RA-56 | n8n | -- | Lista |
| TAR-39 | Configurar la matriz de escalamiento, el horario y los canales de emergencia | RA-57, RA-58 | Equipo, n8n | TAR-38 | Bloqueada |
| TAR-40 | Reporte anónimo de las preguntas sin respuesta | RA-59 | n8n | TAR-33 | Bloqueada |

## Puntos de partida

Lo que ya se sabe y ahorra trabajo. No cierra ningún requerimiento.

| Tarea | Punto de partida |
|---|---|
| TAR-01 | `model/whatsapp_service.py` tiene fijo que escuche en todas las interfaces y un secreto por defecto público: nada de eso está corregido. El puente es agnóstico al entorno: cada colaborador responde solo por las pruebas en el suyo y debe poder variar su configuración a voluntad. La corrección no puede suponer una red privada, la ausencia de un túnel ni un emulador concreto; hoy la dirección de escucha no es configurable. Variar la configuración no suspende R11. Escenario: ESC-CAN-09 |
| TAR-02 | Ver el cierre de RA-21. Mostrar la demo desde n8n no es por sí misma ninguna de las dos vías de RA-10: el equipo debe elegir una |
| TAR-05 | RA-09 es deuda funcional: no hay mecanismo ni fecha, así que TAR-06 y TAR-30 siguen bloqueadas. Apagar una puerta no espera. Cerrar la decisión no prueba su aplicación: eso son ESC-CAN-08 (TAR-06) y ESC-CAN-10 (TAR-30) |
| TAR-06 | Ver el cierre de RA-21. La puerta Web debe seguir apagada hasta cumplir R11. Escenario: ESC-CAN-08 |
| TAR-30 | Ver el cierre de RA-21. Una puerta apagada sigue apagada hasta cumplir R11. Escenario: ESC-CAN-10 |
| TAR-12 | El portal no lee `capa`. Su parte urgente es el aviso, cuyo escenario ya existe: ESC-CAN-07 |
| TAR-14 | Una opción, no un requisito: que el portal pida primero la respuesta local (`solo_local`, RA-41) y escale después |
| TAR-16 | En n8n local o sobre una copia, sin reactivar puertas del servidor. Corregir una brecha no espera a reproducirla; si sigue sin corregir, la reproducción sirve de prueba que falla |
| TAR-17 | El PR #15 probó el caso con una copia del nodo, no con el Cerebro real: por eso sigue abierto |
| TAR-19 | El PR #15 reporta 44 s en una pregunta que fue al Nivel 2, sin indicar si el modelo estaba cargado. El PR #16 reporta las 15 preguntas exactas del FAQ contra la API del servidor; no cubre paráfrasis |
| TAR-22 | Claude Code cargó `AGENTS.md` mediante `CLAUDE.md` en una sesión de VS Code. No se ha hecho la pregunta de control ni se registró la versión; las otras herramientas no se han probado |
| TAR-23 | La prueba afectada es `tests/test_rrhh_api.py::test_reply_response_carries_a_cors_header` |
| TAR-35 | Prebel 5.1 y 2.4. El puente local invita a identificarse: ESC-CAN-03. Escenario nuevo: ESC-CAN-11 |
| TAR-37 | El juego de preguntas y sus resultados contienen datos reales: quedan fuera del repositorio (R1, R15) |
| TAR-29 | El cierre de RA-21 dice que la puerta Web estaba activa en el servidor; RA-36 y `n8n/scripts/exportar_flujos.py` dicen que aún no existe allí. Confirmar cuál vale. Lo que se exporte debe cumplir R1 |
