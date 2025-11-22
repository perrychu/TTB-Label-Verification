from base64 import b64encode
from fasthtml.common import *
from typing import Any

from ocr_service import LabelOCRService


ocr_service = LabelOCRService()

app, rt = fast_app(hdrs=(picolink,))


def hero_section() -> Div:
    return Div(
        H1("Alcohol Label Verification"),
        P("Upload a label image and enter the expected details to verify compliance."),
        cls="stack"
    )


def input_fields_section(form_data: dict[str, str] | None = None) -> Div:
    form_data = form_data or {}
    return Div(
        H3("Product details"),
        Div(
            Label("Brand name", Input(name="brand_name", value=form_data.get("brand_name", ""), placeholder="e.g., Riverbend Winery")),
            Label("Product name / class", Input(name="product_name", value=form_data.get("product_name", ""), placeholder="e.g., Cabernet Sauvignon")),
            Label(
                "Alcohol by volume (%)",
                Input(name="abv", value=form_data.get("abv", ""), type="number", step="0.1", placeholder="e.g., 13.5")
            ),
            Label("Volume (mL)", Input(name="volume_ml", value=form_data.get("volume_ml", ""), type="number", step="1", placeholder="e.g., 750")),
            cls="stack"
        ),
        cls="card stack"
    )


def image_upload_section() -> Div:
    return Div(
        H3("Label image"),
        Label(
            "Upload image",
            Input(
                name="label_image",
                id="label-image-input",
                type="file",
                accept="image/*",
                required=True,
                hx_post="/preview",
                hx_trigger="change",
                hx_target="#preview-container",
                hx_swap="innerHTML",
                hx_encoding="multipart/form-data",
            )
        ),
        cls="card stack"
    )


def image_preview_section() -> Div:
    return Div(
        H3("Label preview"),
        Div(
            Span("Preview will appear after selection.", id="preview-placeholder"),
            id="preview-container",
            cls="preview"
        ),
        cls="card stack"
    )


def results_section(results: str | None = None, error: str | None = None, **attrs: Any) -> Div:
    content = []
    if error:
        content.append(P(f"Error: {error}", cls="error"))
    elif results:
        content.append(Pre(results, cls="ocr-text"))
    else:
        content.append(P("Results will appear here after you verify a label."))

    return Div(
        H3("Verification results"),
        *content,
        id="results-container",
        cls="card stack",
        **attrs,
    )


def layout(
    ocr_text: str | None = None,
    error: str | None = None,
    form_data: dict[str, str] | None = None,
) -> Div:
    return Div(
        hero_section(),
        Div(
            Div(
                Form(
                    input_fields_section(form_data=form_data),
                    image_upload_section(),
                    Button("Verify label", type="submit"),
                    action="/verify",
                    method="post",
                    enctype="multipart/form-data",
                    hx_post="/verify",
                    hx_target="#results-container",
                    hx_swap="outerHTML",
                    hx_encoding="multipart/form-data",
                    cls="stack"
                ),
                cls="column"
            ),
            Div(
                image_preview_section(),
                results_section(results=ocr_text, error=error),
                cls="column"
            ),
            cls="grid"
        ),
        cls="page stack"
    )


@rt("/")
def get():
    return layout()


@rt("/verify")
async def verify(
    label_image: UploadFile | None = None,
    brand_name: str = "",
    product_name: str = "",
    abv: str = "",
    volume_ml: str = "",
    gov_warning: str = "",
    notes: str = "",
):
    """OCR the image and display the extracted text."""
    form_data = {
        "brand_name": brand_name,
        "product_name": product_name,
        "abv": abv,
        "volume_ml": volume_ml,
        "gov_warning": gov_warning,
        "notes": notes,
    }

    if not label_image:
        return (
            results_section(error="Please upload a label image.")
        )

    content = await label_image.read()
    if not content:
        return (
            results_section(error="Uploaded file was empty.")
        )

    try:
        ocr_text = ocr_service.extract_text_from_image(content)
    except Exception as exc:
        return (
            results_section(error=f"OCR failed: {exc}")
        )

    if not ocr_text:
        return (
            results_section(error="No text detected in the uploaded image.")
        )

    return (
        results_section(results=ocr_text)
    )


@rt("/preview")
async def preview(label_image: UploadFile | None = None):
    """HTMX endpoint to render an image preview when a file is selected."""
    if not label_image:
        return Div(
            Span("Preview will appear after selection.", id="preview-placeholder"),
            results_section(hx_swap_oob="true"),
        )

    content = await label_image.read()
    if not content:
        return Div(
            Span("Preview will appear after selection.", id="preview-placeholder"),
            results_section(hx_swap_oob="true"),
        )

    # Inline the selected image using a data URL so we don't need to persist it.
    encoded = b64encode(content).decode("ascii")
    data_url = f"data:{label_image.content_type};base64,{encoded}"
    return Div(
        Img(src=data_url, cls="preview-img", style="max-width:100%; height:auto;"),
        results_section(hx_swap_oob="true"),
    )


serve()
