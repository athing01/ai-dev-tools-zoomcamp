# MVP Backlog

## 1. Card input form and validation

**Goal:** Create a Django form and page for collecting all specified business-card inputs.

**Acceptance criteria:**

- Supports primary language (Thai or English), names, Thai/English roles and company names, address, phone, email, social links, QR destination URL, orientation, photo choice, and optional photo upload.
- Requires the name in the selected primary language and a valid QR destination URL.
- Applies validation errors on the form; no business-card data is stored in the database.
- Has automated tests for required fields and invalid URL handling.

**Constraints:** Use Django `forms.Form`, not models or migrations.

## 2. In-memory QR-code generator

**Goal:** Generate a PNG QR code from a validated destination URL.

**Acceptance criteria:**

- Provides a small, reusable Python function/service.
- Produces a valid in-memory PNG image for a URL.
- Has automated tests that verify an image is produced.

**Constraints:** Add only the required QR-code dependency through `uv`; do not host or create destination URLs.

## 3. PNG business-card renderer

**Goal:** Render supplied card data, optional photo, and QR code into a single PNG image.

**Acceptance criteria:**

- Supports portrait and landscape orientations.
- Supports each required combination: with/without photo in each orientation.
- Includes supplied card information and the QR code.
- Renders Thai and English card text with an implementation font that supports both; there is no user-facing font customisation.
- Produces an in-memory PNG and has focused renderer tests.

**Constraints:** Use an image-rendering dependency managed by `uv`; do not persist rendered cards or uploads.

## 4. Card-generation endpoint and download flow

**Goal:** Connect the validated form, QR generator, and renderer so users can download the result.

**Acceptance criteria:**

- A valid submission returns a PNG response with an appropriate download filename and `image/png` content type.
- Invalid submissions redisplay the form with errors.
- The integration flow works for all four layout combinations.
- Automated integration tests cover a valid download and an invalid submission.

**Constraints:** No accounts, authentication, database-backed card storage, profile pages, or non-PNG output.
