# TTB Label Verification

FastHTML web application that recreates a simplified Alcohol and Tobacco Tax and Trade Bureau (TTB) label review. Users submit the expected label fields and an image, the backend runs OCR through Google Cloud Vision, and the app reports where the label agrees or diverges from the submission.

## Feature Highlights
- **Rich comparison strategy** – 3-tier matching strategy with match reasoning feedback enabling users to quickly & transparently evaluate output quality. Tier 1 is exact text match; Tier 2 is normalized match adjusting for capitalization, punctuation, and spacing variation; Tier 3 is fuzzy match. Best fuzzy match score and substring are shown as additional user context for Tier 3 matches and no-match. All matching strategies incorporate word boundaries to avoid spurious partial-token matches.
- **User-friendly UX** – FastHTML + USWDS styles keep the layout simple; HTMX endpoints (`/preview`, `/verify`) avoid full page reloads. Outputs formatted to be easily interpretable.
- **Government warning coverage** – Validates presence of the heading and statutory paragraphs individually to handle varying formatting.

## Local Setup
1. **Install dependencies in virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Provide Google Vision credentials**
   Setup a Google cloud project, create service account with access to Cloud Vision API (e.g. assign `Cloud Vision AI Service Agent` role), and generate a credentials JSON. [Google instructions](https://docs.cloud.google.com/vision/docs/setup)

   Credentials JSON will look something like:
   ```
   {
   "type": "service_account",
   "project_id": "<project name>",
   "private_key_id": "<alphanumeric id>",
   "private_key": "...",
   "client_email": "<project email>",
   "client_id": "<numeric id>",
   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
   "token_uri": "https://oauth2.googleapis.com/token",
   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
   "client_x509_cert_url": "<url associated with project>",
   "universe_domain": "googleapis.com"
   }

   ```

   Then, make credentials available locally, either:
   - Set an environment variable `GOOGLE_APPLICATION_CREDENTIALS_JSON` to the credentials json content
   - Save the credentials JSON as a file `GOOGLE_APPLICATION_CREDENTIALS.json` at the project root
3. **Run the development server**
   ```bash
   python main.py
   ```
4. Visit `http://localhost:5001/` in browser

## Using the App
1. **Upload a label** – Drag-and-drop or select a JPEG/PNG. The preview route renders the image inline so the user can confirm they uploaded the right artwork.
2. **Collect data** – Form captures fields to be verified: `Brand Name`, `Product Type/Class`, `ABV %`, and `Volume`.
3. **Run OCR** – App calls Google Vision API and returns full label text for downstream checks.
4. **Verify fields** – `verify_all` normalizes OCR output, cascades through exact/normalized/fuzzy comparisons, and records match details for each input field plus the government warning text.
5. **Report back** – HTMX swaps the result panel with a table that outlines match success/fail and includes commentary (e.g., closest fuzzy match when a field fails).

## Testing
Basic unit test are in `tests/`

Run with
```
python -m pytest tests/
```

## Files
| File | Purpose |
| --- | --- |
| `main.py` | FastHTML routes, HTMX interactions, and UI building blocks. |
| `ocr_service.py` | Google Vision client bootstrap and cached OCR helpers. |
| `verification.py` | VerificationInput dataclass, normalization utilities, per-field validators, and overall orchestration. |
| `Examples/` | Example label images from `ttb.gov` used for manual testing |
| `static/` |  US web design system files for UI formatting |
| `tests/` | Unit tests |