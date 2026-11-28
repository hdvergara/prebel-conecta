# Instrumento: revisar un cambio

**Entrada:** un diff, una rama o un PR. Sirve mejor si revisa un asistente
distinto del que escribió el cambio.

## Pasos

1. Parte de que **cada afirmación del cambio es falsa** y trata de demostrarlo
   con el código o ejecutando algo.
2. Comprueba que cada escenario diga lo mismo que su prueba. Que la prueba
   exista no basta: léela.
3. Busca datos reales en el diff (R1), superficies que queden alcanzables (R11)
   y texto generado que pueda pasar por FAQ (R10).
4. Aplica [`transitividad.md`](transitividad.md).
5. Compara los documentos del cambio con el código, no entre sí.

## Entrega

Por cada hallazgo: archivo y línea, el fallo concreto que provoca, y si está
**confirmado** (lo reprodujiste o lo leíste) o es **posible**. Ordena por
gravedad. Si no encuentras nada, di qué revisaste y qué no.

No modifiques archivos: solo informa.
