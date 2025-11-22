from fasthtml.common import *

app, rt = fast_app(hdrs=(picolink,))


def hero_section() -> Div:
    return Div(
        H1("Alcohol Label Verification"),
        P("Upload a label image and enter the expected details to verify compliance."),
        cls="stack"
    )


def input_fields_section() -> Div:
    return Div(
        H3("Product details"),
        Div(
            Label("Brand name", Input(name="brand_name", placeholder="e.g., Riverbend Winery")),
            Label("Product name / class", Input(name="product_name", placeholder="e.g., Cabernet Sauvignon")),
            cls="stack"
        ),
        Div(
            Label("Alcohol by volume (%)", Input(name="abv", type="number", step="0.1", placeholder="e.g., 13.5")),
            Label("Volume (mL)", Input(name="volume_ml", type="number", step="1", placeholder="e.g., 750")),
            cls="stack"
        ),
        Label(
            "Government warning text",
            Textarea(name="gov_warning", placeholder="Include the full warning text as it should appear on the label.")
        ),
        Label(
            "Notes (optional)",
            Textarea(name="notes", placeholder="Any extra context about the label or packaging.")
        ),
        cls="card stack"
    )


def image_upload_section() -> Div:
    return Div(
        H3("Label image"),
        P("Accepted formats: JPG, PNG. Keep file sizes reasonable for faster OCR."),
        Label(
            "Upload image",
            Input(name="label_image", id="label-image-input", type="file", accept="image/*", required=True)
        ),
        cls="card stack"
    )


def image_preview_section() -> Div:
    return Div(
        H3("Image preview"),
        Div(
            Img(id="image-preview", cls="preview-img", style="display:none; max-width:100%; height:auto;"),
            Span("Preview will appear after selection.", id="preview-placeholder"),
            cls="preview"
        ),
        cls="card stack"
    )


def results_section() -> Div:
    return Div(
        H3("Verification results"),
        P("Results will appear here after you verify a label."),
        cls="card stack"
    )


def layout() -> Div:
    return Div(
        hero_section(),
        Div(
            Div(
                Form(
                    input_fields_section(),
                    image_upload_section(),
                    Button("Verify label", type="submit"),
                    action="/verify",
                    method="post",
                    enctype="multipart/form-data",
                    cls="stack"
                ),
                cls="column"
            ),
            Div(
                image_preview_section(),
                results_section(),
                cls="column"
            ),
            cls="grid"
        ),
        Script(
            """
            (() => {
              const input = document.getElementById("label-image-input");
              const img = document.getElementById("image-preview");
              const placeholder = document.getElementById("preview-placeholder");
              if (!input || !img || !placeholder) return;
              input.addEventListener("change", () => {
                const file = input.files && input.files[0];
                if (!file) {
                  img.style.display = "none";
                  img.removeAttribute("src");
                  placeholder.style.display = "block";
                  return;
                }
                const url = URL.createObjectURL(file);
                img.src = url;
                img.onload = () => URL.revokeObjectURL(url);
                img.style.display = "block";
                placeholder.style.display = "none";
              });
            })();
            """
        ),
        cls="page stack"
    )


@rt("/")
def get():
    return layout()


@rt("/verify")
def post():
    """OCR the image and verify the input form against the OCR text, then display results."""
    return layout()


serve()
