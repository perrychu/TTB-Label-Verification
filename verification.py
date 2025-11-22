import re

from dataclasses import dataclass

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
    text = re.sub(r'[.,\-()_\[\]]', ' ', text) # Replace punctuation with single space
    text = re.sub(r'\s+', ' ', text) # Replace multiple spaces with a single space
    return text

def check_contains(target_text:str, source_text:str) -> VerificationResult:
    """Check if target text is contained in source text."""
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
    result = check_contains(f"{expected,}%", ocr_text)
    return result

def verify_volume_ml(expected:str, ocr_text:str) -> VerificationResult:
    """Check volume text (mL) for exact numeric string."""
    result = check_contains(expected, ocr_text)
    return result

def verify_gov_warning(ocr_text:str) -> VerificationResult:
    """Check for government warning text."""

    title_text = "GOVERNMENT WARNING"
    pregnancy_text = "According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects" 
    drive_health_text = "Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems"

    title_result = check_contains(title_text, ocr_text)
    pregnancy_result = check_contains(pregnancy_text, ocr_text)
    drive_health_result = check_contains(drive_health_text, ocr_text)

    results = [title_result, pregnancy_result, drive_health_result]

    output = VerificationResult(
        match=all(result.match for result in results),
        expected="\n".join(result.expected for result in results),
        found="\n".join(result.expected if result.match else "[missing]" for result in results),
        comment="Government warning text matched" if title_result.match and pregnancy_result.match and drive_health_result.match else "Government warning text did not match"
    )

    return output

def verify_all(input_data: VerificationInput, ocr_text:str) -> dict[str, VerificationResult]:
    """Verify all fields and return results as a dictionary of attribute -> result"""
    ocr_text_norm = normalize_text(ocr_text)

    brand_name_result = verify_brand(input_data.brand_name, ocr_text_norm)
    product_name_result = verify_product_type(input_data.product_name, ocr_text_norm)
    abv_result = verify_abv(input_data.abv, ocr_text_norm)
    volume_ml_result = verify_volume_ml(input_data.volume, ocr_text_norm)
    gov_warning_result = verify_gov_warning(ocr_text_norm)

    return {
        "brand_name": brand_name_result,
        "product_name": product_name_result,
        "abv": abv_result,
        "volume_ml": volume_ml_result,
        "gov_warning": gov_warning_result,
    }
