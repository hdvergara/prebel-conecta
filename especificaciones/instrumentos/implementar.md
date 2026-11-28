# Instrumento: implementar una especificación

**Entrada:** un archivo en `../cambios/` con sus decisiones ya tomadas. Si
quedan pendientes, detente y pídelas.

## Pasos

1. Lee el contexto afectado y sus pruebas.
2. Escribe la prueba de cada escenario y **comprueba que falla** por la razón
   esperada.
3. Implementa lo mínimo para que pase. No agregues lo que ningún escenario pide.
4. Corre las tres suites. Una comprobación saltada no cuenta (R12).
5. Si el escenario necesita un modelo, un servidor o n8n reales, di qué se
   comprobó a mano y qué quedó sin comprobar.
6. Consolida: pasa los escenarios al contexto con su evidencia, actualiza
   `FLUJOS.md`, cierra el requerimiento y borra el archivo del cambio.

**Entrega:** el resumen de lo cambiado, los resultados de las suites y lo no
verificado.

**No hagas commit, push ni despliegues si no te lo piden (R15).**
