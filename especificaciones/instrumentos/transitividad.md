# Instrumento: revisar la transitividad

El principio y el procedimiento son R0 en
[`CONSTITUTION.md`](../../CONSTITUTION.md); léelos allí. El ejemplo formal está
en [`DECISIONES.md`](../../DECISIONES.md#ejemplo-formal-de-r0).

**Entrada:** el cambio propuesto a una regla, una definición, un comportamiento
o un documento del que algo depende.

## Pasos

1. Sigue el procedimiento de R0.
2. **Intenta demostrar que hay un conflicto**, no que no lo hay. Para cada
   concepto pregunta: ¿qué permite ahora este texto que antes no?, ¿qué deja sin
   respaldo?, ¿qué pasa si quien lo lee no sabe qué datos hay detrás?
3. Busca los enlaces que no comparten palabras ni citas: definiciones,
   excepciones, listas, valores por defecto y notas dentro de los flujos.
4. Aplica el cambio también a tu propio texto nuevo.
5. Ejecuta las pruebas de documentación. Si la trazabilidad falla, revisa lo que
   señala **antes** de actualizar `tests/trazabilidad.json`.

## Entrega

| Cadena | Qué obligan juntos sus eslabones | Qué regla choca | Cómo se resuelve |
|---|---|---|---|

Declara las cadenas sin resolución. Que las pruebas pasen no demuestra que no
haya conflictos: comparan archivos, no significados.
