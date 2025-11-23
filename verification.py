from dataclasses import dataclass
import logging

from rapidfuzz import fuzz, process
import regex

logger = logging.getLogger(__name__)

@dataclass
class VerificationInput:
    brand_name: str
    product_type: str
    abv: str
    volume: str

@dataclass
class VerificationResult:
    match: bool
    expected: str
    comment: str

def normalize_text(text:str) -> str:
    """Normalize punctuation and spacing for consistent comparisons.

    Args:
        text: Raw string extracted from the form or OCR output.

    Returns:
        Lowercase string where punctuation becomes single spaces and whitespace is collapsed.
    """
    text = text.strip().lower()
    text = regex.sub(r"[.,\-()_\[\]]", " ", text) # Replace punctuation with single space
    text = regex.sub(r"\s+", " ", text) # Replace multiple spaces with a single space
    return text


def substrings_by_similar_character_length(string:str, character_length:int):
    """Generate substrings near the desired character length.

    Args:
        string: Source text to slice.
        character_length: Target number of characters for each substring.

    Returns:
        List of substrings with lengths within one character of the target.
    """
    substrings = []
    for length in range(character_length - 1, character_length + 2):
        if length > 0 and length < len(string):
            substrings.extend(string[i:i+length] for i in range(len(string) - length + 1))
    return substrings


def substrings_by_similar_token_length(string:str, token_length:int):
    """Generate substrings near the desired token length.

    Args:
        string: Source text to slice on whitespace boundaries.
        token_length: Target number of tokens for each substring.

    Returns:
        List of substrings whose token counts are within one token of the target.
    """
    tokens = string.split()
    substrings = []
    for length in range(token_length - 1, token_length + 2):
        if length > 0 and length < len(tokens):
            substrings.extend(" ".join(tokens[i:i+length]) for i in range(len(tokens) - length + 1))
    return substrings


def check_exact(target_text:str, source_text:str) -> VerificationResult:
    """Compare exact verbatim text match in the OCR output.

    Args:
        target_text: Text entered by the user.
        source_text: Full OCR text to search through.

    Returns:
        VerificationResult indicating whether an exact match was found.
    """
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            comment="Target text is empty"
        )

    #Check for whitespace instead of word boundaries (\b) due to '% ' not counting
    match = regex.search(fr"(?<=^|\s){target_text}(?=$|\s)", source_text) is not None

    return VerificationResult(
        match=match,
        expected=target_text,
        comment="Exact match" if match else "No match"
    )


def check_normalized(target_text:str, source_text:str) -> VerificationResult:
    """Compare normalized strings to tolerate punctuation, capitalization, and spacing differences.

    Args:
        target_text: Text entered by the user.
        source_text: Full OCR text to search through.

    Returns:
        VerificationResult indicating whether the normalized texts match.
    """
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            comment="Target text is empty"
        )

    target_text_norm = normalize_text(target_text)
    source_text_norm = normalize_text(source_text)
    #Check for whitespace instead of word boundaries (\b) due to '% ' not counting
    match = regex.search(fr"(?<=^|\s){target_text_norm}(?=$|\s)", source_text_norm) is not None

    return VerificationResult(
        match=match,
        expected=target_text,
        comment="Normalized text match" if match else "No match"
    )


def check_fuzzy(target_text:str, source_text:str) -> VerificationResult:
    """Compare fuzzy matching similarity against token-based substrings.

    Args:
        target_text: Text entered by the user.
        source_text: Full OCR text to search through.

    Returns:
        VerificationResult detailing the best fuzzy score and match decision.
    """
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            comment="Target text is empty"
        )

    target_text_norm = normalize_text(target_text)
    source_text_norm = normalize_text(source_text)

    best_text, best_ratio, _ = process.extract(
        target_text_norm,
        substrings_by_similar_token_length(source_text_norm, len(target_text_norm.split())), 
        limit=1,
        scorer=fuzz.ratio)[0]
    best_ratio = round(best_ratio, 1)
    match = best_ratio >= 92

    return VerificationResult(
        match=match,
        expected=target_text,
        comment=f"Fuzzy match: '{best_text}' ({best_ratio}%)" if match else f"No match. Closest text: '{best_text}' ({best_ratio}%)"
    )


def check_matches_cascade(target_text:str, source_text:str) -> VerificationResult:
    """Run increasingly fuzzy strategies until a match is found or all fail.

    Args:
        target_text: Text entered by the user.
        source_text: Full OCR text to search through.

    Returns:
        VerificationResult from the best successful strategy, or no match
        with comment indicating the closest (unsuccessful) fuzzy match.
    """
    if not target_text or not source_text:
        return VerificationResult(
            match=False,
            expected=target_text,
            comment="Target text is empty"
        )
    
    for check_func in [check_exact, check_normalized, check_fuzzy]:
        result = check_func(target_text, source_text)
        if result.match:
            return result
    
    return result


def verify_brand(expected:str, ocr_text:str) -> VerificationResult:
    """Validate that the OCR contains the submitted brand name.

    Args:
        expected: Brand name entered by the user.
        ocr_text: Raw OCR output for the label.

    Returns:
        VerificationResult describing the match status for the brand field.
    """
    result = check_matches_cascade(expected, ocr_text)
    return result

def verify_product_type(expected:str, ocr_text:str) -> VerificationResult:
    """Validate that the OCR contains the submitted product type.

    Args:
        expected: Product type entered by the user.
        ocr_text: Raw OCR output for the label.

    Returns:
        VerificationResult describing the match status for the product type field.
    """
    result = check_matches_cascade(expected, ocr_text)
    return result

def verify_abv(expected:str, ocr_text:str) -> VerificationResult:
    """Validate that the OCR contains the submitted ABV with a percent suffix.

    Args:
        expected: Alcohol by volume value entered by the user.
        ocr_text: Raw OCR output for the label.

    Returns:
        VerificationResult describing the match status for the ABV field.
    """
    result = check_matches_cascade(f"{expected}%", ocr_text)
    return result

def verify_volume(expected:str, ocr_text:str) -> VerificationResult:
    """Validate that the OCR contains the submitted volume information.

    Args:
        expected: Volume value entered by the user.
        ocr_text: Raw OCR output for the label.

    Returns:
        VerificationResult describing the match status for the volume field.
    """
    result = check_matches_cascade(expected, ocr_text)
    return result

def verify_gov_warning(ocr_text:str) -> VerificationResult:
    """Validate that the full government warning text appears in the OCR output.

    Args:
        ocr_text: Raw OCR output for the label.

    Returns:
        VerificationResult describing whether the full government warning text 
        matched or what parts were missing.
    """

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
        comment="Full government warning found" if all_matched else f"Sections not found: {'\n'.join(result.expected for result in results if not result.match)}"
    )

def verify_all(input_data: VerificationInput, ocr_text:str) -> dict[str, VerificationResult]:
    """Run every verification check and collate the results.

    Args:
        input_data: Structured values submitted by the user.
        ocr_text: Raw OCR output for the label.

    Returns:
        Dictionary mapping each field name to its VerificationResult.
    """
    ocr_text_norm = normalize_text(ocr_text)

    brand_name_result = verify_brand(input_data.brand_name, ocr_text_norm)
    product_type_result = verify_product_type(input_data.product_type, ocr_text_norm)
    abv_result = verify_abv(input_data.abv, ocr_text_norm)
    volume_result = verify_volume(input_data.volume, ocr_text_norm)
    gov_warning_result = verify_gov_warning(ocr_text_norm)

    return {
        "brand_name": brand_name_result,
        "product_type": product_type_result,
        "abv": abv_result,
        "volume": volume_result,
        "warning": gov_warning_result,
    }
