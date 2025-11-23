from base64 import b64encode
from fasthtml.common import *
from typing import Any
import logging

from ocr_service import LabelOCRService
from verification import VerificationInput, VerificationResult, verify_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
app, rt = fast_app(
    pico=False,
    hdrs=(
        Script(src="static/js/uswds-init.min.js"),
        Link(rel="stylesheet", href="static/css/uswds.min.css", type='text/css'),
    ),
)
ocr_service = LabelOCRService()


def format_newlines(text:str) -> FT:
    """Convert text block with newlines to html format (stacked paragraph tags).

    Args:
        text: Plain string with newline separators.

    Returns:
        FastHTML Div element containing each line in its own paragraph.
    """
    return Div(P(line) for line in text.split("\n"))


def title_section() -> FT:
    """Build html for the title and description section.

    Args:
        None.

    Returns:
        FastHTML Div element with heading and helper text.
    """
    return Div(
        H1("Alcohol Label Verification"),
        P("Upload a label image and enter the expected details to verify compliance. All fields are required.", cls="usa-hint"),
    )


def input_fields_section(form_data: dict[str, str] | None = None):
    """Build html for input form of label text to be verified.

    Args:
        form_data: Optional prefills for the label fields.

    Returns:
        FastHTML Div containing the labeled input controls.
    """
    form_data = form_data or {}
    return Div(
        H2("Fields to verify"),
        Div(
            Label(
                "Brand name",
                for_="brand_name_input",
                cls="usa-label"
            ),
            Input(
                    name="brand_name",
                    id="brand_name_input",
                    value=form_data.get("brand_name", ""),
                    placeholder="e.g., Riverbend Winery",
                    required=True,
                    cls="usa-input"
            ),
            Label(
                "Product type / class",
                Input(
                    name="product_type",
                    value=form_data.get("product_type", ""),
                    placeholder="e.g., Cabernet Sauvignon",
                    required=True,
                    cls="usa-input"
                ),
                cls="usa-label"
            ),
            Label(
                "Alcohol by volume (%)",
                Input(
                    name="abv",
                    value=form_data.get("abv", ""),
                    type="number", step="0.1",
                    placeholder="e.g., 13.5",
                    required=True,
                    cls="usa-input"
                ),
                cls="usa-label"
            ),
            Label(
                "Volume",
                Input(
                    name="volume",
                    value=form_data.get("volume", ""),
                    placeholder="e.g., 750 ml, 12 fl oz, etc.",
                    required=True,
                    cls="usa-input"
                ),
                cls="usa-label"
            ),
            cls="usa-form-group"
        ),
    )


def image_upload_section() -> FT:
    """Build html for the label image upload input. Element includes HTMX
    to update the preview container when an image is uploaded.

    Returns:
        FastHTML Div containing the file input with HTMX hooks.
    """
    return Div(
        H2("Label"),
        Label(
            "Upload image (jpg or png)",
            Input(
                name="label_image",
                id="label-image-input",
                type="file",
                accept="image/*",
                multiple=False,
                required=True,
                hx_post="/preview",
                hx_trigger="change",
                hx_target="#preview-container",
                hx_swap="innerHTML",
                hx_encoding="multipart/form-data",
                cls="usa-file-input"
            )
        )
    )


def image_preview_section() -> FT:
    """Build html for a placeholder container to show a preview of the uploaded label.

    Returns:
        FastHTML Div that holds the preview placeholder and target container.
    """
    return Div(
        H2("Label preview"),
        Div(
            Span("Preview will display after a label image is selected.", id="preview-placeholder"),
            id="preview-container",
        )
    )


def results_section(content: FT | None = None, error: str | None = None, **attrs: Any) -> FT:
    """Build html for the results container, optionally showing error or custom content.

    Args:
        content: FastHTML fragment to render inside the section when available.
        error: Error message to display if error occurs before validation.
        **attrs: Additional attributes forwarded to the results Div.

    Returns:
        FastHTML Div ready to slot into the layout or respond to HTMX swaps.
    """
    if error:
        content=P(f"Error: {error}", cls="error")
    elif content:
        content = content
    else:
        content=P("Results will display after submitting an image and fields to verify.")

    return Div(
        H2("Verification results"),
        content,
        id="results-container",
        **attrs,
    )


def verification_results_detail(results: dict[str, VerificationResult]) -> FT:
    """Build html fragment to show a summary of verification results.

    Args:
        results: Mapping of field names to their VerificationResult objects.

    Returns:
        FastHTML Div element with summary text and a results table.
    """

    mismatches = sum(1 for result in results.values() if not result.match)

    if mismatches == 0:
        result_title = "✅ Success! Label fully verified."
    else:
        result_title = f"❌ Error: {mismatches} of {len(results)} fields don't match."
    
    detail_rows = []

    for key, result in results.items():
        field_name = key.replace("_", " ").title()
        icon = "✅ Yes" if result.match else "❌ No"

        detail_rows.append(
            Tr(
                Th(field_name, scope="row"),
                Td(icon),
                Td(format_newlines(result.expected)),
                Td(format_newlines(result.comment)),
                cls=f"check-item"
            )
        )

    return Div(
        H3(result_title),
        Table(
            Thead(
                Tr(
                    Th("Field", scope="col"),
                    Th("Match?", scope="col"),
                    Th("Expected text", scope="col"),
                    Th("Comment", scope="col"),
                )
            ),
            Tbody(*detail_rows),
            cls="usa-table"
        ),
    )


@rt("/")
def get(
    ocr_text: str | None = None,
    error: str | None = None,
    form_data_prefill: dict[str, str] | None = None,
) -> FT:
    """Compose the entire page layout including form, preview, and results areas.
    Includes HTMX to update the results container when the user clicks to submit
    the verification request.

    Args:
        ocr_text: Optional OCR output to display in the initial results pane.
        error: Optional error message to surface immediately.
        form_data_prefill: Prefill values for the verification form inputs.

    Returns:
        FastHTML Body object representing the full UI.
    """

    return Body(
        title_section(),
        Div(
            Div(
                Form(
                    image_upload_section(),
                    input_fields_section(form_data=form_data_prefill),
                    Button("Verify label", type="submit", cls="usa-button"),
                    action="/verify",
                    method="post",
                    enctype="multipart/form-data",
                    hx_post="/verify",
                    hx_target="#results-container",
                    hx_swap="outerHTML",
                    hx_encoding="multipart/form-data",
                ),
                cls="column grid-col-5",
            ),
            Div(
                image_preview_section(),
                results_section(results=[P(ocr_text)] if ocr_text else None, error=error),
                cls="column grid-col-fill"
            ),
            cls="grid grid-row grid-gap"
        ),
        Script(src="static/js/uswds.min.js"),
        cls="grid-container",
    )


@rt("/preview")
async def preview(label_image: UploadFile | None = None):
    """Build html for the preview of the uploaded label image.

    Args:
        label_image: UploadFile provided by HTMX when the user selects an image.

    Returns:
        FastHTML Div updating the preview container and resetting results.
    """
    if not label_image:
        return Div(
            Span("Preview will display after a label image is selected.", id="preview-placeholder"),
            results_section(hx_swap_oob="true"),
        )

    content = await label_image.read()
    if not content:
        return Div(
            Span("Preview will display after a label image is selected.", id="preview-placeholder"),
            results_section(hx_swap_oob="true"),
        )

    # Inline the selected image using a data URL so we don't need to persist it.
    encoded = b64encode(content).decode("ascii")
    data_url = f"data:{label_image.content_type};base64,{encoded}"
    return Div(
        Img(src=data_url, cls="preview-img", style="max-width:100%; height:auto;"),
        results_section(hx_swap_oob="true"),
    )


@rt("/verify")
async def verify(
    label_image: UploadFile | None = None,
    brand_name: str = "",
    product_type: str = "",
    abv: str = "",
    volume: str = ""
):
    """Run OCR on the uploaded label and build html for the verification results.

    Args:
        label_image: Uploaded image to be processed by the OCR service.
        brand_name: Expected brand name provided by the user.
        product_type: Expected product class provided by the user.
        abv: Expected ABV value provided by the user.
        volume: Expected container volume provided by the user.

    Returns:
        FastHTML Div showing verification success, mismatches, or errors.
    """
    
    if not label_image:
        return results_section(error="Please upload a label image.")

    content = await label_image.read()
    if not content:
        return results_section(error="Uploaded file was empty.")

    try:
        logger.info("Calling OCR")
        ocr_text = ocr_service.extract_text_from_image(content)
        logger.info(f"OCR text: {ocr_text}")
    except Exception as exc:
        return results_section(error=f"OCR failed: {exc}")

    if not ocr_text:
        return results_section(error="No text detected in the uploaded image.")

    form_input = VerificationInput(brand_name=brand_name, product_type=product_type, abv=abv, volume=volume)
    logger.info(f"Checking input: {form_input}")
    verification_results = verify_all(form_input, ocr_text)
    logger.info(f"Verification results: {verification_results}")

    results_detail = verification_results_detail(verification_results)

    return (
        results_section(content=results_detail)
    )


serve()
