# Contexto: canales

**Propósito:** llevar preguntas y respuestas por cada canal, sin decidir la
cadena de la API.

**Depende de:** faq

## Módulos

| Archivo | Papel |
|---|---|
| `model/whatsapp_service.py` | Puente local de WhatsApp |
| `model/empleados_mock.json` | Personas ficticias del puente y del portal (R4) |

También pertenecen a este contexto, sin ser módulos de Python: el recuadro del
asistente y la burbuja de chat en `dist/`, y los flujos de `n8n/workflows/`.

**Responsables:** n8n lo trabaja una persona; el portal, otra.

**Consume:** `RRHHBot.match()` en el puente local; `POST /reply` por red en el
portal y en el Cerebro. El detalle está en [`FLUJOS.md`](../../FLUJOS.md).

**Reglas que aplican:** R2, R3, R4, R6, R7, R10, R11.

## Escenarios

| ID | Escenario | Evidencia |
|---|---|---|
| ESC-CAN-01 | Dada la API inalcanzable, cuando se pregunta en el portal, entonces muestra el texto de respaldo, indica que no hay confianza ni sentimiento y no ofrece una acción (R2) | `e2e/tests/model-box.spec.js::an unreachable local API degrades to the static fallback message` |
| ESC-CAN-02 | Dado un webhook con firma inválida, cuando llega al puente, entonces se rechaza | `tests/test_whatsapp_service.py::test_incoming_message_with_invalid_signature_is_rejected` |
| ESC-CAN-03 | Dado un remitente sin identificar, cuando pregunta por un dato propio, entonces recibe la respuesta del FAQ y una invitación a identificarse (R7) | `tests/test_whatsapp_service.py::test_unidentified_sender_gets_the_match_plus_a_self_identification_invite` |
| ESC-CAN-04 | Dada la URL del chat sin configurar, cuando se abre el portal, entonces la burbuja no se carga (R5) | `e2e/tests/chat-bubble.spec.js::still does not load with the demo flag, while the webhook URL is an unconfigured placeholder` |
| ESC-CAN-05 | Dada una respuesta de la API con texto generado o sin origen, cuando la recibe el Cerebro, entonces no la usa como FAQ (R10) | RA-15 |
| ESC-CAN-06 | Dada una respuesta del FAQ con marcadores, cuando la recibe el Cerebro, entonces sigue al Nivel 2 | RA-12 |
| ESC-CAN-07 | Dado texto generado, cuando lo muestra el portal, entonces avisa que lo escribió una IA o no lo usa (R10) | RA-39 |
| ESC-CAN-08 | Dada una puerta de n8n activa, cuando la alcanza alguien no controlado, entonces se rechaza antes de procesar (R11) | RA-09 |
| ESC-CAN-09 | Dado el puente local, cuando está en marcha, entonces nadie no controlado lo alcanza (R11) | RA-20 |
