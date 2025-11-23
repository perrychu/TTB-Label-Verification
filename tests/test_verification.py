import sys
from pathlib import Path

import pytest

from verification import (  # noqa: E402
    VerificationInput,
    normalize_text,
    check_matches_cascade,
    verify_abv,
    verify_brand,
    verify_volume,
    verify_gov_warning,
    verify_all,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  Old  Tom Distillery  ", "old tom distillery"),
        ("45% Alc./Vol. (90 Proof)", "45% alc vol 90 proof"),
        ("NET\tCONTENTS\n750 mL", "net contents 750 ml"),
    ],
)
def test_normalize_text_collapses_whitespace_and_punctuation(raw, expected):
    """Incoming OCR text often varies in spacing/punctuation; ensure normalization is predictable."""
    assert normalize_text(raw) == expected


def test_check_matches_cascade_recovers_from_fuzzy_match():
    """Cascade should fall back to fuzzy matching when exact/normalized comparisons fail."""
    ocr_text = normalize_text("OLD TOM DISTILERY Bourbon Whiskey")
    result = check_matches_cascade("Old Tom Distillery", ocr_text)
    assert result.match is True
    assert "Fuzzy match" in result.comment


def test_verify_abv_appends_percent():
    """ABV comparison adds a percent sign, so the OCR text must include the units."""
    ocr = normalize_text("This label includes 13.5% alc by volume")
    result = verify_abv("13.5", ocr)
    assert result.match is True


def test_verify_brand_reports_mismatch_details():
    """Mismatched brand names should surface the closest fuzzy suggestion."""
    ocr = normalize_text("RIVER BEND BREWING CO.")
    result = verify_brand("Riverbend Winery", ocr)
    assert result.match is False
    assert "Closest text" in result.comment


@pytest.mark.parametrize(
    "query,target,match_result",
    [
        ("750 ml", "10% ABV 750 mL volume", True),
        ("750 ml", "10% ABV 750 ML volume", True),
        ("750  ml", "10% ABV 750 ml volume", True),
        ("700 ml", "10% ABV 750 ml volume", False),
        ("75 ml", "10% ABV 750 ml volume", False),
        ("50 ml", "10% ABV 750 ml volume", False),
        ("7500 ml", "10% ABV 750 ml volume", False),
        ("12.4 fl oz", "10% ABV 124 fl oz volume", False),
        ("124 fl oz", "10% ABV 12.4 fl oz volume", False),
    ],
)
def test_check_volume_edge_cases(query, target, match_result):
    """Check that near-match edge cases are handled correctly."""
    assert verify_volume(query, target).match == match_result


def test_verify_government_warning_requires_all_sections():
    """Full government warning check should fail if any subsection is missing."""
    partial_warning = normalize_text(
        "GOVERNMENT WARNING: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects."
    )
    result = verify_gov_warning(partial_warning)
    assert result.match is False
    assert "Sections not found" in result.comment


def test_verify_all_returns_expected_mapping():
    """End-to-end verification should populate results for every field."""
    ocr = normalize_text(
        """
        OLD TOM DISTILLERY
        Kentucky Straight Bourbon Whiskey
        45% Alc./Vol. (90 Proof)
        Net Contents 750 mL
        GOVERNMENT WARNING:
        1. According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects.
        2. Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
        """
    )
    data = VerificationInput(
        brand_name="Old Tom Distillery",
        product_type="Kentucky Straight Bourbon Whiskey",
        abv="45",
        volume="750 ml",
    )
    results = verify_all(data, ocr)

    assert set(results.keys()) == {"brand_name", "product_type", "abv", "volume", "warning"}
    assert all(result.match for result in results.values())
