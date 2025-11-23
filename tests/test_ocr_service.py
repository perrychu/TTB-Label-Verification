import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ocr_service import LabelOCRService  # noqa: E402


def make_service():
    """Create a LabelOCRService instance without running __init__."""
    return LabelOCRService.__new__(LabelOCRService)


def test_load_credentials_prefers_env_json(monkeypatch):
    """_load_credentials should pull from the env var when JSON is provided."""
    svc = make_service()
    fake_creds = object()
    monkeypatch.setenv("TEST_CREDS_ENV", '{"client_email":"user@example.com"}')
    monkeypatch.setattr(
        "ocr_service.service_account.Credentials.from_service_account_info",
        lambda info: fake_creds,
    )

    result = svc._load_credentials("TEST_CREDS_ENV", "unused.json")
    assert result is fake_creds


def test_load_credentials_falls_back_to_file(monkeypatch, tmp_path):
    """If the env var is empty, _load_credentials should use the provided file path."""
    svc = make_service()
    fake_creds = object()
    creds_path = tmp_path / "service.json"
    # File existence isn't checked because we stub the loader, but create it for clarity.
    creds_path.write_text("{}")
    monkeypatch.delenv("TEST_CREDS_ENV", raising=False)
    monkeypatch.setattr(
        "ocr_service.service_account.Credentials.from_service_account_file",
        lambda path: fake_creds,
    )

    result = svc._load_credentials("TEST_CREDS_ENV", str(creds_path))
    assert result is fake_creds


def test_load_credentials_missing_sources_raises(monkeypatch):
    """When neither env nor file path are available, a ValueError should be raised."""
    svc = make_service()
    monkeypatch.delenv("TEST_CREDS_ENV", raising=False)
    with pytest.raises(ValueError):
        svc._load_credentials("TEST_CREDS_ENV", None)


def test_extract_text_from_file_reads_bytes(tmp_path):
    """Ensure extract_text_from_file forwards raw bytes into the cached image helper."""
    svc = make_service()
    fake_bytes = b"label-bytes"
    image_path = tmp_path / "label.png"
    image_path.write_bytes(fake_bytes)
    svc.extract_text_from_image = MagicMock(return_value="OK")

    result = LabelOCRService.extract_text_from_file(svc, str(image_path))

    svc.extract_text_from_image.assert_called_once_with(fake_bytes)
    assert result == "OK"


def test_extract_text_from_image_returns_full_text(monkeypatch):
    """Happy path: Vision returns annotations and we return the first description."""
    svc = make_service()
    fake_response = SimpleNamespace(
        error=SimpleNamespace(message=""),
        text_annotations=[
            SimpleNamespace(description="Hello\nWorld"),
            SimpleNamespace(description="Hello"),
        ],
    )
    svc.client = MagicMock(text_detection=MagicMock(return_value=fake_response))
    monkeypatch.setattr("ocr_service.vision.Image", lambda content: SimpleNamespace(content=content))

    result = LabelOCRService.extract_text_from_image(svc, b"bytes-1")

    assert result == "Hello\nWorld"
    svc.client.text_detection.assert_called_once()


def test_extract_text_from_image_raises_on_api_error(monkeypatch):
    """Vision error messages should bubble up as RuntimeError."""
    svc = make_service()
    fake_response = SimpleNamespace(
        error=SimpleNamespace(message="quota exceeded"),
        text_annotations=[],
    )
    svc.client = MagicMock(text_detection=MagicMock(return_value=fake_response))
    monkeypatch.setattr("ocr_service.vision.Image", lambda content: SimpleNamespace(content=content))

    with pytest.raises(RuntimeError, match="quota exceeded"):
        LabelOCRService.extract_text_from_image(svc, b"bytes-2")


def test_extract_text_from_image_returns_none_when_empty(monkeypatch):
    """No annotations should result in None."""
    svc = make_service()
    fake_response = SimpleNamespace(
        error=SimpleNamespace(message=""),
        text_annotations=[],
    )
    svc.client = MagicMock(text_detection=MagicMock(return_value=fake_response))
    monkeypatch.setattr("ocr_service.vision.Image", lambda content: SimpleNamespace(content=content))

    result = LabelOCRService.extract_text_from_image(svc, b"bytes-3")

    assert result is None
