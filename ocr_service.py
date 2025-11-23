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
        """Initialize the OCR client with optional credential overrides.

        Args:
            credentials_env_var: Environment variable that may contain JSON credentials.
            credentials_path: Path to a service account file used when the env var is absent.

        Returns:
            None. Sets up `self.client` for downstream OCR calls.
        """
        credentials = self._load_credentials(credentials_env_var, credentials_path)
        if credentials:
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            self.client = vision.ImageAnnotatorClient()

    def _load_credentials(
        self, credentials_json_env: str, credentials_file_path: str
    ) -> Optional[service_account.Credentials]:
        """Construct service-account credentials from JSON env var or a file.

        Args:
            credentials_json_env: Environment variable to inspect for embedded JSON.
            credentials_file_path: Filesystem path to a service account JSON file fallback.

        Returns:
            Instantiated `Credentials` object if created 
            
        Raises:
            ValueError: If no credentials source is available.
        """
        json_env_value = os.getenv(credentials_json_env)
        if json_env_value:
            try:
                info = json.loads(json_env_value)
                return service_account.Credentials.from_service_account_info(info)
            except Exception as exc:
                raise ValueError("Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON") from exc

        if credentials_file_path:
            return service_account.Credentials.from_service_account_file(credentials_file_path)

        raise ValueError(f"No credentials found in {credentials_json_env} or {credentials_file_path}")

    def extract_text_from_file(self, file_path: str) -> str | None:
        """Load an image from disk and run OCR on its bytes.

        Args:
            file_path: Absolute or relative path to an image file.

        Returns:
            Detected text string or None when OCR finds no content.
        """
        with open(file_path, "rb") as f:
            return self.extract_text_from_image(f.read())
    
    @lru_cache(maxsize=100)
    def extract_text_from_image(self, image_bytes: bytes) -> str | None:
        """Call Google Vision to detect text directly from image bytes.

        Args:
            image_bytes: Raw image data in memory.

        Returns:
            Detected text string or None when nothing is detected.
        """
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
