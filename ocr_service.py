from functools import lru_cache
import json
import os
from typing import Optional

from google.cloud import vision
from google.oauth2 import service_account


class LabelOCRService:
    """Google Vision helper for extracting label text."""

    def __init__(
        self,
        credentials_env_var: str = "GOOGLE_APPLICATION_CREDENTIALS_JSON",
        credentials_path: str = "GOOGLE_APPLICATION_CREDENTIALS.json",
    ):
        credentials = self._load_credentials(credentials_env_var, credentials_path)
        if credentials:
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            self.client = vision.ImageAnnotatorClient()

    def _load_credentials(
        self, credentials_json_env: str, credentials_file_path: str
    ) -> Optional[service_account.Credentials]:
        json_env_value = os.getenv(credentials_json_env)
        if json_env_value:
            try:
                info = json.loads(json_env_value)
                return service_account.Credentials.from_service_account_info(info)
            except Exception as exc:
                raise ValueError("Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON") from exc

        if credentials_file_path:
            return service_account.Credentials.from_service_account_file(credentials_file_path)

        raise ValueError(f"No credentials found in {credentials_json_env} or {credentials_path}")

    def extract_text_from_file(self, file_path: str) -> str | None:
        """Extract text from a file."""
        with open(file_path, "rb") as f:
            return self.extract_text_from_image(f.read())
    
    @lru_cache(maxsize=100)
    def extract_text_from_image(self, image_bytes: bytes) -> str | None:
        """Run OCR on an image and return the full detected text."""
        if not image_bytes:
            return None

        image = vision.Image(content=image_bytes)
        response = self.client.text_detection(image=image)

        if response.error and response.error.message:
            raise RuntimeError(f"Vision API error: {response.error.message}")

        annotations = response.text_annotations
        if not annotations:
            return None

        # First entry contains the full text; others are per-segment.
        return annotations[0].description.strip()
