import re
import logging

from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VerificationInput:
    brand_name: str
    product_name: str
    abv: str
    volume: str

@dataclass
class VerificationResult:
    match: bool
    expected: str
    found: str
    comment: str | None = None

def normalize_text(text:str) -> str:
    """Normalize text for comparison."""
    text = text.strip().lower()
    text = re.sub(r"[.,\-()_\[\]]", " ", text) # Replace punctuation with single space
    text = re.sub(r"\s+", " ", text) # Replace multiple spaces with a single space
    return text

def check_exact(target_text:str, source_text:str) -> VerificationResult:
    """Check if target text is exactly contained in source text."""
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            found="",
            comment="Target text is empty"
        )
    
    match = target_text in source_text

    return VerificationResult(
        match=match,
        expected=target_text,
        found=target_text if match else "",
        comment="Exact match" if match else "No match"
    )

def check_normalized(target_text:str, source_text:str) -> VerificationResult:
    """Check if normalized target text is contained in normalized source text."""
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            found="",
            comment="Target text is empty"
        )

    target_text_norm = normalize_text(target_text)
    source_text_norm = normalize_text(source_text)
    match = target_text_norm in source_text_norm

    return VerificationResult(
        match=match,
        expected=target_text,
        found=target_text_norm if match else "",
        comment="Normalized text match" if match else "No match"
    )

def check_matches_cascade(target_text:str, source_text:str) -> VerificationResult:
    """Try text matching with decreasing precision"""
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            found="",
            comment="Target text is empty"
        )
    
    for check_func in [check_exact, check_normalized]:
        result = check_func(target_text, source_text)
        if result.match:
            return result
    
    return VerificationResult(
        match=False,
        expected=target_text,
        found="",
        comment="No match"
    )


def verify_brand(expected:str, ocr_text:str) -> VerificationResult:
    """Check label OCR for brand name form value."""
    result = check_matches_cascade(expected, ocr_text)
    return result

def verify_product_type(expected:str, ocr_text:str) -> VerificationResult:
    """Check label OCR for product type form value."""
    result = check_matches_cascade(expected, ocr_text)
    return result

def verify_abv(expected:str, ocr_text:str) -> VerificationResult:
    """Check label OCR for ABV form value."""
    result = check_matches_cascade(f"{expected}%", ocr_text)
    return result

def verify_volume(expected:str, ocr_text:str) -> VerificationResult:
    """Check label OCR for volume form value."""
    result = check_matches_cascade(expected, ocr_text)
    return result

def verify_gov_warning(ocr_text:str) -> VerificationResult:
    """Check for government warning text."""

    title_text = "GOVERNMENT WARNING"
    pregnancy_text = "According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects" 
    drive_health_text = "Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems"

    title_result = check_matches_cascade(title_text, ocr_text)
    pregnancy_result = check_matches_cascade(pregnancy_text, ocr_text)
    drive_health_result = check_matches_cascade(drive_health_text, ocr_text)

    results = [title_result, pregnancy_result, drive_health_result]

    all_matched = all(result.match for result in results)

    return VerificationResult(
        match=all_matched,
        expected="\n".join(result.expected for result in results),
        found="",
        comment="Full government warning found" if all_matched else f"Sections not found: {'\n'.join(result.expected for result in results if not result.match)}"
    )

def verify_all(input_data: VerificationInput, ocr_text:str) -> dict[str, VerificationResult]:
    """Verify all fields and return results as a dictionary of attribute -> result"""
    ocr_text_norm = normalize_text(ocr_text)

    brand_name_result = verify_brand(input_data.brand_name, ocr_text_norm)
    product_name_result = verify_product_type(input_data.product_name, ocr_text_norm)
    abv_result = verify_abv(input_data.abv, ocr_text_norm)
    volume_ml_result = verify_volume(input_data.volume, ocr_text_norm)
    gov_warning_result = verify_gov_warning(ocr_text_norm)

    return {
        "brand_name": brand_name_result,
        "product_name": product_name_result,
        "abv": abv_result,
        "volume_ml": volume_ml_result,
        "gov_warning": gov_warning_result,
    }
