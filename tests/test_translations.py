import pytest
from translations import TRANSLATIONS, LANG_OPTIONS, LANG_CODE_MAP, get_text


def test_translation_languages():
    expected_langs = {"es", "en", "fr", "zh", "ko", "it", "pt"}
    assert set(TRANSLATIONS.keys()) == expected_langs


def test_get_text_default():
    # Test valid key in Spanish
    text_es = get_text("es", "kpi_lmp")
    assert "Houston LMP" in text_es

    # Test missing key fallback
    text_fallback = get_text("es", "non_existent_key_123")
    assert text_fallback == "non_existent_key_123"


def test_get_text_formatting():
    text = get_text("es", "alert_high_body", lmp=150.5, threshold=100.0)
    assert "$150.50" in text
    assert "$100.00" in text


def test_lang_options_map():
    assert LANG_OPTIONS["es"] == "🇨🇴 Español"
    assert LANG_CODE_MAP["🇨🇴 Español"] == "es"
