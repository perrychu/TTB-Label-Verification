class LabelOCRService:
    def __init__(self):
        # Load credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON env var
        # If not set, try GOOGLE_APPLICATION_CREDENTIALS file path
        # use google.oauth2.service_account.Credentials.from_service_account_info()
        # Create vision.ImageAnnotatorClient with credentials
        pass
    
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        # Use google.cloud.vision.ImageAnnotatorClient
        # Use client.text_detection() to extract text
        # Return texts[0].description (full text)
        # Handle errors and empty results
        pass