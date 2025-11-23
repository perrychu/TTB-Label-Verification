import sys
from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

import main  # noqa: E402

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_preview_returns_placeholder_when_no_file():
    """Preview endpoint should instruct users when no file is provided."""
    fragment = await main.preview()
    assert "Preview will display after a label image is selected." in str(fragment)


async def test_preview_returns_image_when_file_uploaded():
    """Preview should render an inline data URL when bytes are supplied."""
    upload = UploadFile(filename="label.png", file=BytesIO(b"fake-bytes"), headers={"content-type": "image/png"})
    fragment = await main.preview(label_image=upload)
    html = str(fragment)
    assert "data:image/png;base64" in html
    assert "<img" in html.lower()


async def test_verify_requires_image():
    """Submitting verification without an image should return an error."""
    fragment = await main.verify()
    assert "Please upload a label image." in str(fragment)


async def test_verify_returns_success_table(monkeypatch):
    """Successful OCR flow should render the success header and table rows."""
    upload = UploadFile(filename="label.png", file=BytesIO(b"image-bytes"), headers={"content-type": "image/png"})
    ocr_text = """
    OLD TOM DISTILLERY
    Kentucky Straight Bourbon Whiskey
    45% Alc./Vol. (90 Proof)
    750 mL
    GOVERNMENT WARNING:
    According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects.
    Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
    """

    monkeypatch.setattr(main.ocr_service, "extract_text_from_image", lambda _: ocr_text)

    fragment = await main.verify(
        label_image=upload,
        brand_name="Old Tom Distillery",
        product_type="Kentucky Straight Bourbon Whiskey",
        abv="45",
        volume="750 mL",
    )

    html = str(fragment)
    assert "Success! Label fully verified" in html
    assert "Brand Name" in html
