# Especificaciones

Qué debe hacer cada contexto del dominio. Aquí se trabaja con **especificación
primero** (R14 de [`CONSTITUTION.md`](../CONSTITUTION.md)) y **diseño guiado por
el dominio**, sin mover el código.

> No confundir con `specs/` ni `.specs/`: son las carpetas de **documentos
> reales** de Prebel, ignoradas por git (R1). Nada de ellas se copia aquí.

## Contenido

| Archivo | Para qué |
|---|---|
| [`dominio.md`](dominio.md) | Lenguaje común y mapa de contextos |
| [`TAREAS.md`](TAREAS.md) | Plan de trabajo derivado de los requerimientos abiertos |
| [`contextos/faq.md`](contextos/faq.md) | FAQ y coincidencia |
| [`contextos/respuesta.md`](contextos/respuesta.md) | Decidir qué respuesta se entrega |
| [`contextos/retroalimentacion.md`](contextos/retroalimentacion.md) | Cola y reuso |
| [`contextos/canales.md`](contextos/canales.md) | Portal, WhatsApp y n8n |
| [`cambios/PLANTILLA.md`](cambios/PLANTILLA.md) | Plantilla para especificar un cambio |
| [`instrumentos/`](instrumentos/README.md) | Cómo trabajan los asistentes de IA, con cualquier herramienta |

## Qué va en cada sitio

Una especificación describe lo esperado. No crea reglas ni autoriza lo que una
regla prohíbe, y no repite lo que ya vive en otro nivel: las reglas se citan por
su ID, el comportamiento detallado y sus diagramas están en
[`FLUJOS.md`](../FLUJOS.md) y los umbrales, en `model/arquitectura.json`.

## Ciclo de un cambio

1. **Requerimiento:** parte de un punto de
   [`REQUERIMIENTOS_ABIERTOS.md`](../REQUERIMIENTOS_ABIERTOS.md), o se agrega.
2. **Especificar:** copia la plantilla a `cambios/RA-NN-nombre.md`. Define los
   escenarios y los contextos afectados.
3. **R0:** si toca una regla o una definición, sigue su procedimiento.
4. **Probar:** escribe la prueba de cada escenario y comprueba que falla.
5. **Implementar** hasta que las tres suites estén en verde (R12).
6. **Consolidar:** pasa los escenarios al contexto, actualiza `FLUJOS.md`, cierra
   el requerimiento y borra el archivo de `cambios/`.

Excepción (R14): reducir exposición, como apagar una superficie o restringir el
acceso, no espera a la especificación. Se actualiza después.

## Cómo se escribe un escenario

`| ESC-XXX-NN | Dado…, cuando…, entonces… | evidencia |`

La evidencia es una de estas:
- una prueba automática, `ruta/archivo.py::nombre_de_prueba`, o
  `e2e/tests/archivo.spec.js::título exacto`;
- un requerimiento, `RA-NN`: **abierto** si falta implementar o probar, o
  **cerrado** si su cierre registra una comprobación manual.

`tests/test_especificaciones.py` comprueba que la evidencia exista, que cada
archivo de `model/` pertenezca a un solo contexto y que las dependencias entre
contextos sean las declaradas. No comprueba que una prueba cubra de verdad lo
que dice su escenario: eso se revisa.

## Reparto entre responsables

Quien maneja n8n y quien maneja el portal y la API trabajan por separado. El
contrato que comparten está en `FLUJOS.md`; cambiarlo afecta a ambos y lo
revisan los dos.
