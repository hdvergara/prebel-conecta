# Contexto: faq

**Propósito:** mantener el FAQ ficticio y decir cuál de sus respuestas se parece
a una pregunta.

**Depende de:** retroalimentacion

## Módulos

| Archivo | Papel |
|---|---|
| `model/rrhh_bot.py` | Coincidencia, tipo y sentimiento |
| `model/entrenar.py` | Calibración y revisión manual (herramienta fuera de línea) |
| `model/faq_rrhh.json` | Entradas del FAQ, única fuente de su contenido |

**Publica:** `RRHHBot.match()`. No conoce al orquestador, al conector ni al
reuso (R9).

**Reglas que aplican:** R1, R5, R9.

## Escenarios

| ID | Escenario | Evidencia |
|---|---|---|
| ESC-FAQ-01 | Dada una pregunta igual a una registrada, cuando se compara, entonces devuelve la respuesta, la ruta y el área de esa entrada | `tests/test_rrhh_bot.py::test_match_exact_phrasing_returns_the_matched_entry` |
| ESC-FAQ-02 | Dada una pregunta parecida pero bajo el corte, cuando se compara, entonces no responde con esa entrada | `tests/test_rrhh_bot.py::test_near_miss_below_threshold_escalates_to_rrhh` |
| ESC-FAQ-03 | Dado un mensaje sin coincidencia y con tono negativo, cuando se compara, entonces responde atendiendo el tono | `tests/test_rrhh_bot.py::test_negative_sentiment_with_no_faq_match_returns_grosero_not_fallback` |
| ESC-FAQ-04 | Dado un saludo sin pregunta, cuando se compara, entonces saluda y no usa el respaldo | `tests/test_rrhh_bot.py::test_greeting_with_no_faq_match_returns_saludo_not_fallback` |
| ESC-FAQ-05 | Dada una pregunta que solo comparte palabras clave con un tema, cuando se compara, entonces pide acotarla | `tests/test_rrhh_bot.py::test_keyword_overlap_without_a_close_embedding_match_asks_to_narrow` |
| ESC-FAQ-06 | Dados dos temas casi empatados, cuando la pregunta nombra uno, entonces gana ese | `tests/test_rrhh_bot.py::test_tied_topics_are_resolved_by_a_distinguishing_word_in_the_text` |
| ESC-FAQ-07 | Dada la capa de coincidencia, entonces no importa al orquestador ni al conector | `tests/test_arquitectura.py::test_rrhh_bot_never_imports_the_llm_connector_or_the_orchestrator` |
| ESC-FAQ-08 | Dada una entrada con marcadores, cuando se muestra, entonces no se presentan huecos al usuario | RA-13 |
