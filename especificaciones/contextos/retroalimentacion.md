# Contexto: retroalimentacion

**Propósito:** guardar lo que el conector resolvió y las capas anteriores no
sabían, para revisarlo y reusarlo.

**Depende de:** respuesta

## Módulos

| Archivo | Papel |
|---|---|
| `model/retroalimentacion.py` | Cola en disco, con escritura segura |
| `model/rag_retroalimentacion.py` | Búsqueda por similitud para reusar |

**Publica:** `registrar()`, `listar_pendientes()` y `buscar_similar()`. El reuso
recibe el modelo de embeddings por inyección (R9).

**Reglas que aplican:** R1, R5, R8, R9, R10.

## Escenarios

| ID | Escenario | Evidencia |
|---|---|---|
| ESC-RET-01 | Dada una pregunta que las capas anteriores no sabían, cuando el conector la responde, entonces queda en la cola | `tests/test_orquestador.py::test_llm_answer_for_a_low_confidence_question_is_queued_as_feedback` |
| ESC-RET-02 | Dada una respuesta que ya se conocía con confianza, cuando se escala a pedido, entonces no se encola | `tests/test_orquestador.py::test_llm_answer_is_not_queued_when_the_ml_already_had_it_with_confidence` |
| ESC-RET-03 | Dada una pregunta parecida a una de la cola, cuando se escala, entonces se reusa sin llamar al conector | `tests/test_orquestador.py::test_a_similar_already_answered_question_is_reused_without_calling_the_connector` |
| ESC-RET-04 | Dado un fallo al escribir la cola, cuando el conector responde, entonces la respuesta se entrega igual (R8) | `tests/test_orquestador.py::test_a_feedback_queue_failure_never_breaks_the_llm_answer` |
| ESC-RET-05 | Dados registros simultáneos, cuando se escriben, entonces no se pierde ninguno | `tests/test_retroalimentacion.py::test_concurrent_registrar_calls_do_not_lose_either_entry` |
| ESC-RET-06 | Dada una cola con contenido dañado, cuando se lee, entonces se trata como vacía | `tests/test_retroalimentacion.py::test_listar_pendientes_recovers_from_a_corrupted_file` |
| ESC-RET-07 | Dada una entrada mal formada, cuando se busca, entonces no se rompe la cadena | `tests/test_rag_retroalimentacion.py::test_never_raises_if_an_entry_is_malformed` |
| ESC-RET-08 | Dada una entrada revisada, cuando se lleva al FAQ, entonces cumple R1 y R5 | RA-35 |
