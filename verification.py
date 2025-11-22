import re

from dataclasses import dataclass


@dataclass
class VerificationResult:
    match: bool
    expected: str
    source: str
    found: str
    comment: str | None = None

def normalize_text(text:str) -> str:
    """Normalize text for comparison."""
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text) # Replace multiple spaces with a single space
    text = re.sub(r'[.,-()_\[\]]', ' ', text) # Replace punctuation with single space
    return text

def check_contains(target_text:str, source_text:str) -> VerificationResult:
    """Check if target text is contained in source text."""
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            source=source_text,
            found="",
            comment="Target text is empty"
        )

    target_text_norm = normalize_text(target_text)
    source_text_norm = normalize_text(source_text)
    match = target_text_norm in source_text_norm

    return VerificationResult(
        match=match,
        expected=target_text,
        source=source_text,
        found=target_text_norm if match else "",
        comment="Normalized text matched" if match else "Normalized text did not match"
    )

def verify_brand(expected:str, ocr_text:str) -> VerificationResult:
    """Check brand name with exact, case-insensitive match."""
    result = check_contains(expected, ocr_text)
    return result

def verify_product_type(expected:str, ocr_text:str) -> VerificationResult:
    """Check product type with exact, case-insensitive match."""
    result = check_contains(expected, ocr_text)
    return result

def verify_abv(expected:str, ocr_text:str) -> VerificationResult:
    result = check_contains(expected, ocr_text)
    return result

def verify_volume_ml(expected:str, ocr_text:str) -> VerificationResult:
    """Check volume text (mL) for exact numeric string."""
    result = check_contains(expected, ocr_text)
    return result

def verify_all(form_data:dict[str, str], ocr_text:str) -> dict[str, VerificationResult]:
    """Verify all fields and return results as a dictionary of attribute -> result"""
    ocr_text_norm = normalize_text(ocr_text)

    brand_name_result = verify_brand(form_data.get("brand_name", ""), ocr_text_norm)
    product_name_result = verify_product_type(form_data.get("product_name", ""), ocr_text_norm)
    abv_result = verify_abv(form_data.get("abv", ""), ocr_text_norm)
    volume_ml_result = verify_volume_ml(form_data.get("volume_ml", ""), ocr_text_norm)

    return {
        "brand_name": brand_name_result,
        "product_name": product_name_result,
        "abv": abv_result,
        "volume_ml": volume_ml_result,
    }
