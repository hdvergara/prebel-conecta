"""Unit tests for model/orquestador.py's threshold ladder (95%/75%,
pedir_continuar, y caída controlada cuando el conector no responde).

Ni el bot real ni un servidor MCP real hacen falta aquí: un bot y un
conector fake bastan para probar la lógica de la cadena -- la calidad del
embedding y la conexión MCP en vivo son responsabilidad de otras suites
(test_rrhh_bot.py, y verificación manual contra un servidor MCP real).
"""
import json

import pytest

from orquestador import Orquestador


class BotFalso:
    """Devuelve el mismo resultado de match() para cualquier texto, con la
    confianza fijada en el constructor -- lo único que le importa a la
    cadena del orquestador."""

    def __init__(self, confianza, tipo="confiado", ruta="ruta-x", area="area-x", guia="Guía X."):
        self._resultado = {
            "respuesta": "Respuesta del ML.", "ruta": ruta, "area": area,
            "confianza": confianza, "sentimiento": {"etiqueta": "neutral", "estrellas": 3, "confianza": 0.5},
            "guia": guia, "tipo": tipo,
        }

    def match(self, text):
        return dict(self._resultado)


class ConectorFalso:
    def __init__(self, respuesta="Respuesta del LLM."):
        self.respuesta = respuesta
        self.llamadas = []

    def responder(self, pregunta, contexto):
        self.llamadas.append((pregunta, contexto))
        return self.respuesta


class ConectorQueNuncaResponde:
    def responder(self, pregunta, contexto):
        return None


# Context: un Orquestador construido con un bot y un conector fake.

def test_confianza_above_95_is_answered_directly_without_touching_the_connector():
    """Given confianza = 0.97 (sobre el umbral predictivo).
    When responder_pregunta() se llama.
    Then responde con lo que ya tenía el ML, capa='predictivo', y el
    conector LLM nunca se consulta."""
    conector = ConectorFalso()
    orq = Orquestador(BotFalso(confianza=0.97), conector)
    resultado = orq.responder_pregunta("una pregunta cualquiera")
    assert resultado["capa"] == "predictivo"
    assert resultado["respuesta"] == "Respuesta del ML."
    assert conector.llamadas == []


def test_confianza_between_75_and_95_uses_the_ml_answer_as_is():
    """Given confianza = 0.80 (entre los dos umbrales).
    When responder_pregunta() se llama.
    Then responde con la respuesta del ML, capa='ml', sin escalar al LLM."""
    conector = ConectorFalso()
    orq = Orquestador(BotFalso(confianza=0.80), conector)
    resultado = orq.responder_pregunta("otra pregunta")
    assert resultado["capa"] == "ml"
    assert conector.llamadas == []


def test_confianza_below_75_escalates_to_the_llm_connector():
    """Given confianza = 0.40 (bajo el umbral del LLM).
    When responder_pregunta() se llama.
    Then la respuesta final es la del conector, capa='llm', tipo='generado',
    y ruta/area/guia que el ML ya tenía calculados se conservan."""
    conector = ConectorFalso(respuesta="Respuesta generada por el LLM.")
    orq = Orquestador(BotFalso(confianza=0.40, ruta="ruta-x", area="area-x", guia="Guía X."), conector)
    resultado = orq.responder_pregunta("una pregunta dificil")
    assert resultado["respuesta"] == "Respuesta generada por el LLM."
    assert resultado["capa"] == "llm"
    assert resultado["tipo"] == "generado"
    assert resultado["ruta"] == "ruta-x"
    assert resultado["area"] == "area-x"
    assert resultado["guia"] == "Guía X."
    assert conector.llamadas == [("una pregunta dificil", {"ruta": "ruta-x", "area": "area-x"})]


def test_connector_unavailable_falls_back_gracefully_to_the_ml_answer():
    """Given confianza = 0.40, pero el conector no responde (None).
    When responder_pregunta() se llama.
    Then no se deja al usuario sin nada -- se usa lo que el ML ya tenía,
    capa='ml', igual que el principio de caída controlada de R2/R8."""
    orq = Orquestador(BotFalso(confianza=0.40), ConectorQueNuncaResponde())
    resultado = orq.responder_pregunta("pregunta sin respuesta del llm")
    assert resultado["capa"] == "ml"
    assert resultado["respuesta"] == "Respuesta del ML."


def test_a_feedback_queue_failure_never_breaks_the_llm_answer(monkeypatch):
    """Given confianza = 0.40 (escala al LLM, que responde) y registrar()
    lanza algo que no es OSError (p. ej. TimeoutError, si el lock de
    model/retroalimentacion.py quedó colgado).
    When responder_pregunta() se llama.
    Then la respuesta del LLM se devuelve igual -- esta cola es una
    comodidad, nunca debe tumbar una respuesta que ya está lista."""
    import orquestador

    monkeypatch.setattr(orquestador, "registrar", lambda *a, **k: (_ for _ in ()).throw(TimeoutError("lock colgado")))
    conector = ConectorFalso(respuesta="Respuesta del LLM a pesar del fallo de la cola.")
    orq = Orquestador(BotFalso(confianza=0.40), conector)
    resultado = orq.responder_pregunta("una pregunta cualquiera")
    assert resultado["respuesta"] == "Respuesta del LLM a pesar del fallo de la cola."
    assert resultado["capa"] == "llm"


def test_pedir_continuar_skips_the_threshold_and_goes_straight_to_the_llm():
    """Given confianza = 0.97 (normalmente respondería directo), pero
    pedir_continuar=True (el usuario pidió seguir buscando).
    When responder_pregunta() se llama.
    Then escala al conector LLM sin importar el umbral."""
    conector = ConectorFalso(respuesta="Respuesta generada, pedida a propósito.")
    orq = Orquestador(BotFalso(confianza=0.97), conector)
    resultado = orq.responder_pregunta("quiero mas detalle", pedir_continuar=True)
    assert resultado["capa"] == "llm"
    assert conector.llamadas != []


def test_llm_answer_for_a_low_confidence_question_is_queued_as_feedback(tmp_path, monkeypatch):
    """Given confianza = 0.40 (las capas anteriores no tenían esta
    respuesta) y el conector sí responde.
    When responder_pregunta() se llama.
    Then la pregunta/respuesta queda registrada en la cola de
    retroalimentación, para revisión manual -- no se escribe sola en
    faq_rrhh.json (ver model/retroalimentacion.py)."""
    import retroalimentacion

    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    conector = ConectorFalso(respuesta="Respuesta nueva del LLM.")
    orq = Orquestador(BotFalso(confianza=0.40), conector)
    orq.responder_pregunta("una pregunta que el ml no sabia")

    pendientes = json.loads((tmp_path / "retroalimentacion.json").read_text(encoding="utf-8"))
    assert len(pendientes) == 1
    assert pendientes[0]["pregunta"] == "una pregunta que el ml no sabia"
    assert pendientes[0]["respuesta"] == "Respuesta nueva del LLM."


def test_llm_answer_is_not_queued_when_the_ml_already_had_it_with_confidence(tmp_path, monkeypatch):
    """Given confianza = 0.90 (el ML ya la tenía con confianza, sobre
    UMBRAL_LLM), pero pedir_continuar=True fuerza igual la escalada al LLM,
    y el conector responde.
    When responder_pregunta() se llama.
    Then NO se registra como retroalimentación: las capas anteriores ya
    tenían esta respuesta con confianza, no es información nueva."""
    import retroalimentacion

    monkeypatch.setattr(retroalimentacion, "RUTA", tmp_path / "retroalimentacion.json")
    conector = ConectorFalso()
    orq = Orquestador(BotFalso(confianza=0.90, tipo="confiado"), conector)
    orq.responder_pregunta("pregunta ya conocida por el ml", pedir_continuar=True)

    assert retroalimentacion.listar_pendientes() == []
