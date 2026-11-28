# Prebel Conecta: demostración

> **Desactualizado (RA-49).** Este recorrido describe una versión del portal que
> `dist/index.html` no carga hoy. No lo uses para preparar una demostración; para
> el portal actual, ver [`README.md`](README.md).

Sitio estático con datos ficticios. El selector representa perfiles; no es autenticación ni autorización de producción. Los casos, contenidos y valoraciones se guardan en localStorage y se comparten únicamente entre perfiles del mismo navegador y origen. No usar datos reales. Sin integración con nómina, IA generativa o WhatsApp.

## Recorrido sugerido (5 minutos)

1. Valentina: buscar “me pagaron menos”, abrir la ficha y solicitar revisión a Nómina.
2. Laura: abrir el caso, pedir información adicional y enviar la respuesta.
3. Valentina: responder desde el historial. Laura: resolver el caso.
4. Mateo: consultar guantes/gafas; contrastar con ergonomía visible para Valentina.
5. Generar un certificado con o sin salario y descargar su PDF. Revisar tres períodos de nómina simulada.
6. Laura: editar una pregunta, guardar borrador y publicar una nueva versión. Comprobar el cambio con un colaborador.
7. Consultar los indicadores y restablecer la demo cuando termine la presentación.

Las vacaciones reservan saldo al registrarse y mantienen la reserva al aprobarse; cancelar o devolver libera esos días. Se cuentan lunes a viernes incluidos festivos. La proyección de 1,25 días/mes es un supuesto ilustrativo. Validar reglas, responsables, permisos, fuentes y tiempos con Prebel.

## Verificación

Ejecutar `node tests/modelo.cjs` y `node tests/documentos.cjs` desde el repositorio. Servir `dist` con `python -m http.server 8895 --directory dist`. GitHub Pages publica `dist` al subir a main.

La biblioteca jsPDF se distribuye localmente con su licencia MIT en `dist/vendor`.
