# Instrumento: especificar un cambio

**Entrada:** un requerimiento (`RA-NN`) o la descripción de lo que se quiere.

## Pasos

1. Lee el requerimiento, el contexto afectado y la parte de `FLUJOS.md` que lo
   describe. Comprueba en el código que el problema sigue existiendo.
2. Si no hay requerimiento, propón agregarlo antes de continuar.
3. Copia [`../cambios/PLANTILLA.md`](../cambios/PLANTILLA.md) a
   `../cambios/RA-NN-nombre.md`.
4. Escribe escenarios que se puedan comprobar, con el lenguaje de
   [`../dominio.md`](../dominio.md). Incluye el fallo y la caída controlada, no
   solo el camino feliz.
5. Indica la evidencia prevista de cada escenario.
6. Aplica [`transitividad.md`](transitividad.md).
7. Marca las decisiones que le corresponden al equipo. No las tomes tú.

**Entrega:** el archivo del cambio y la lista de decisiones pendientes.

**Detente** si el cambio exige incumplir una regla, o si el contrato compartido
cambia y no se sabe quién más debe revisarlo. No escribas código.
