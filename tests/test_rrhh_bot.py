"""Unit tests for RRHHBot's matching/threshold/sentiment logic.

Per CONSTITUTION.md "Harness": the real SentenceTransformer and sentiment
pipeline are replaced with deterministic fakes (fakes.py) so these tests run
in milliseconds, offline, with no model download. They verify RRHHBot's own
logic (threshold comparison, ruta/area passthrough, sentiment bucketing) --
not embedding quality, which is a model-quality concern outside this suite.
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from fakes import FakeSentenceTransformer, FakeSentimentPipeline

FIXTURE = Path(__file__).parent / "fixtures" / "faq_test.json"


@pytest.fixture
def make_bot():
    """Factory fixture: builds an RRHHBot against the fixture FAQ, with its
    heavy models faked."""
    import rrhh_bot

    def _make(sentiment_responses=None):
        with patch.object(rrhh_bot, "SentenceTransformer", return_value=FakeSentenceTransformer()), \
             patch.object(rrhh_bot, "pipeline", return_value=FakeSentimentPipeline(sentiment_responses)):
            return rrhh_bot.RRHHBot(faq_path=FIXTURE)

    return _make


# Context: a bot built from tests/fixtures/faq_test.json (2 generic entries).

def test_match_exact_phrasing_returns_the_matched_entry(make_bot):
    """Given a query identical to one of the FAQ's own registered phrasings.
    When match() is called.
    Then confianza is 1.0 and the entry's respuesta/ruta/area are returned."""
    bot = make_bot()
    result = bot.match("pregunta uno")
    assert result["confianza"] == 1.0
    assert result["respuesta"] == "Respuesta uno"
    assert result["ruta"] == "ruta-uno"
    assert result["area"] == "area-uno"


def test_match_unrelated_text_falls_back(make_bot):
    """Given a query that shares no text with any registered phrasing.
    When match() is called.
    Then confianza stays below THRESHOLD and the generic fallback is returned,
    with ruta/area both null so the frontend renders no dangling action link."""
    bot = make_bot()
    result = bot.match("un texto que no tiene relacion alguna con las preguntas")
    assert result["confianza"] < 0.55
    assert result["respuesta"] == "Fallback de prueba."
    assert result["ruta"] is None
    assert result["area"] is None


def test_reply_is_just_the_matched_text(make_bot):
    """Then reply() returns only match()['respuesta'], for CLI/Teams/Slack
    callers that only want a string, per RRHHBot's own docstring."""
    bot = make_bot()
    assert bot.reply("pregunta dos") == bot.match("pregunta dos")["respuesta"]


@pytest.mark.parametrize("label,expected", [
    ("5 stars", "positivo"), ("4 stars", "positivo"),
    ("3 stars", "neutral"),
    ("2 stars", "negativo"), ("1 star", "negativo"),
])
def test_sentiment_star_bucketing(make_bot, label, expected):
    """Given the pretrained sentiment model's 1-5 star output.
    When sentiment() buckets it.
    Then 1-2 stars -> negativo, 3 -> neutral, 4-5 -> positivo."""
    bot = make_bot({"texto": (label, 0.8)})
    assert bot.sentiment("texto")["etiqueta"] == expected


def test_match_computes_sentiment_even_when_faq_match_fails(make_bot):
    """Given an angry message that matches no FAQ entry.
    When match() is called.
    Then the FAQ side falls back, but sentiment is still computed and
    negative -- the signal the response box surfaces even without a
    confident FAQ match."""
    bot = make_bot({"mensaje furioso sin relacion": ("1 star", 0.7)})
    result = bot.match("mensaje furioso sin relacion")
    assert result["ruta"] is None
    assert result["sentimiento"]["etiqueta"] == "negativo"


def test_fixture_entry_with_explicit_null_ruta_stays_null(make_bot):
    """Given a fixture entry with ruta: null in the source JSON (entry 2).
    When it is the matched entry.
    Then ruta is None (not the string 'null' or omitted) and area still comes
    through, matching the JSON parse of a JSON null."""
    bot = make_bot()
    result = bot.match("pregunta dos")
    assert result["ruta"] is None
    assert result["area"] == "area-dos"
