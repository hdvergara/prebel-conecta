# Contexto: respuesta

**Propósito:** decidir qué respuesta recibe quien pregunta y exponer el contrato
de la API. Es el núcleo del dominio.

**Depende de:** faq, retroalimentacion

## Módulos

| Archivo | Papel |
|---|---|
| `model/orquestador.py` | Cadena de niveles y caída controlada |
| `model/conectores.py` | Interfaz del conector hacia un modelo de lenguaje |
| `model/configuracion.py` | Lectura y validación de los umbrales |
| `model/arquitectura.json` | Umbrales editables |
| `model/rrhh_api.py` | Contrato `POST /reply` |

**Publica:** el contrato de `POST /reply` y el significado de `capa`, definidos
en [`FLUJOS.md`](../../FLUJOS.md) §2.

**Reglas que aplican:** R3, R8, R9, R10, R11.

## Escenarios

| ID | Escenario | Evidencia |
|---|---|---|
| ESC-RES-01 | Dada una coincidencia sobre el umbral predictivo, cuando se pregunta, entonces se entrega sin consultar el conector | `tests/test_orquestador.py::test_confianza_above_95_is_answered_directly_without_touching_the_connector` |
| ESC-RES-02 | Dada una coincidencia entre los dos umbrales, cuando se pregunta, entonces se entrega la respuesta local | `tests/test_orquestador.py::test_confianza_between_75_and_95_uses_the_ml_answer_as_is` |
| ESC-RES-03 | Dada una coincidencia bajo el umbral del conector y sin nada que reusar, cuando se pregunta, entonces se escala al conector | `tests/test_orquestador.py::test_confianza_below_75_escalates_to_the_llm_connector` |
| ESC-RES-04 | Dado un conector que no responde, cuando se escala, entonces se entrega lo que ya había (R8) | `tests/test_orquestador.py::test_connector_unavailable_falls_back_gracefully_to_the_ml_answer` |
| ESC-RES-05 | Dado que quien pregunta pide seguir, cuando se procesa, entonces se omiten los umbrales | `tests/test_orquestador.py::test_pedir_continuar_skips_the_threshold_and_goes_straight_to_the_llm` |
| ESC-RES-06 | Dado `seguir` como texto y no como booleano, cuando llega a la API, entonces no pide seguir | `tests/test_rrhh_api.py::test_reply_treats_a_falsy_looking_string_in_seguir_as_not_asking_to_continue` |
| ESC-RES-07 | Dada una pregunta, cuando la API responde, entonces entrega el contrato completo, incluida `capa` | `tests/test_rrhh_api.py::test_reply_with_text_returns_full_json_contract` |
| ESC-RES-08 | Dado un `text` que no es texto, cuando llega a la API, entonces responde sin error de servidor | `tests/test_rrhh_api.py::test_reply_with_a_non_string_text_is_treated_as_empty_instead_of_500` |
| ESC-RES-09 | Dada una llamada desde otro origen, cuando la API responde, entonces no admite credenciales (R11) | `tests/test_rrhh_api.py::test_cross_origin_access_never_allows_credentials` |
| ESC-RES-10 | Dado el módulo del conector, entonces solo el orquestador lo importa (R9) | `tests/test_arquitectura.py::test_only_the_orchestrator_imports_the_connector_module` |
| ESC-RES-11 | Dado un servidor MCP real, cuando se escala, entonces su respuesta llega por la cadena | RA-26 |
| ESC-RES-12 | Dado un llamador que no quiere escalar, cuando lo indica, entonces no se usan el conector ni la cola | RA-41 |
