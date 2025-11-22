

@dataclass
class VerificationResult:
    match: bool
    expected: str
    found: str

def verify_brand(expected:str, ocr_text:str) -> VerificationResult:
    """Check brand name"""
    pass

def verify_product_type(expected:str, ocr_text:str) -> VerificationResult:
    """Check product type text"""
    pass

def verify_abv(expected:str, ocr_text:str) -> VerificationResult:
    """Check ABV text"""
    pass

def verify_all(form_data:dict[str, str], ocr_text:str) -> dict[str, VerificationResult]:
    """Verify all fields and return results as a dictionary"""
    pass