"""Unit tests for model/configuracion.py's validation of arquitectura.json:
un archivo con JSON sintácticamente válido pero con el tipo equivocado debe
caer a los valores por defecto, igual que un archivo corrupto o ausente --
nunca debe propagar un valor del tipo equivocado (p. ej. un umbral como
string) a quien lo use.
"""
import json

from configuracion import _POR_DEFECTO, _cargar, _validar


# Context: _validar() y _cargar() operan sobre diccionarios/archivos
# construidos directamente en el test, no sobre model/arquitectura.json real.

def test_validar_accepts_a_well_formed_config():
    """Given a dict with the right shape and types.
    When _validar() is called.
    Then it returns the same values, as floats."""
    resultado = _validar({"umbral_predictivo": 0.95, "umbral_llm": 0.75, "orden_capas": ["predictivo", "ml", "llm"]})
    assert resultado == {"umbral_predictivo": 0.95, "umbral_llm": 0.75, "orden_capas": ["predictivo", "ml", "llm"]}


def test_validar_coerces_numeric_strings_to_float():
    """Given thresholds written as numeric strings (valid JSON, wrong type
    for comparisons against a float confidence).
    When _validar() is called.
    Then they come back as real floats, not strings."""
    resultado = _validar({"umbral_predictivo": "0.95", "umbral_llm": "0.75", "orden_capas": ["predictivo"]})
    assert resultado["umbral_predictivo"] == 0.95
    assert isinstance(resultado["umbral_predictivo"], float)


def test_validar_rejects_a_non_numeric_threshold():
    """Given umbral_llm as a non-numeric string.
    When _validar() is called.
    Then it returns None instead of letting a string reach a later
    float comparison."""
    assert _validar({"umbral_predictivo": 0.95, "umbral_llm": "no es un numero", "orden_capas": []}) is None


def test_validar_rejects_thresholds_out_of_the_llm_below_predictivo_order():
    """Given umbral_llm greater than umbral_predictivo (the two don't make
    sense in that order for the chain).
    When _validar() is called.
    Then it returns None."""
    assert _validar({"umbral_predictivo": 0.5, "umbral_llm": 0.9, "orden_capas": []}) is None


def test_validar_rejects_thresholds_outside_zero_to_one():
    """Given a threshold above 1.0.
    When _validar() is called.
    Then it returns None."""
    assert _validar({"umbral_predictivo": 1.5, "umbral_llm": 0.75, "orden_capas": []}) is None


def test_validar_rejects_a_non_list_orden_capas():
    """Given orden_capas as a string instead of a list.
    When _validar() is called.
    Then it returns None."""
    assert _validar({"umbral_predictivo": 0.95, "umbral_llm": 0.75, "orden_capas": "predictivo"}) is None


def test_cargar_falls_back_to_defaults_when_the_file_has_the_wrong_type(tmp_path, monkeypatch):
    """Given arquitectura.json with valid JSON but umbral_llm as a string.
    When _cargar() is called.
    Then the loaded config is exactly the defaults, not a mix with the
    invalid value."""
    import configuracion

    ruta = tmp_path / "arquitectura.json"
    ruta.write_text(json.dumps({"umbral_llm": "no es un numero"}), encoding="utf-8")
    monkeypatch.setattr(configuracion, "RUTA", ruta)
    assert _cargar() == _POR_DEFECTO
