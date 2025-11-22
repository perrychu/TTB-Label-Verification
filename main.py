from fasthtml.common import *

app, rt = fast_app(hdrs=(picolink))


def input_form():
    """HTML form for input fields."""
    return P("Input form")

def image_form():
    """HTML form for image upload. Updates image preview in the UI."""
    return P("Image form")

def verify_button():
    """Button to trigger verification, then display results in the UI"""
    return P("Verify button")

@rt("/")
def get():
    return (
        input_form(),
        image_form(),
        verify_button(),
    )


@rt("/verify")
def post():
    """OCR the image and verify the input form against the OCR text, then display results."""
    pass

serve()