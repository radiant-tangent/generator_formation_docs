# Copilot Prompt: Synthetic Company Formation Document Generator

## Goal

Build a Python CLI pipeline that generates a synthetic dataset of realistic company
formation documents for 5 US states, paired with ground-truth JSON files whose
schema matches a Wells Fargo CRM webform. The dataset will be used to train and
test an Azure Content Understanding model that extracts fields and populates the CRM.

---

## Target States & Document Types

Generate documents for the following state/entity combinations:

| State         | Entity Type | Document Name                | Filing Agency                     |
|---------------|-------------|------------------------------|-----------------------------------|
| Massachusetts | Corp        | Articles of Organization     | Secretary of the Commonwealth     |
| New York      | Corp        | Certificate of Incorporation | NY Dept. of State (DOS)           |
| Delaware      | LLC         | Certificate of Formation     | Division of Corporations          |
| Texas         | LLC         | Certificate of Formation     | Secretary of State (Form 205)     |
| Florida       | Corp        | Articles of Incorporation    | Division of Corporations          |

Download one real blank PDF template per state from the official state agency website
and store them in `templates/` with filenames like `ma_corp_articles.pdf`,
`ny_corp_certificate.pdf`, etc.

---

## Tech Stack

- Python 3.10+
- PyMuPDF (fitz) — PDF rendering and text layer inspection
- Pillow — image manipulation and augmentations
- OpenCV (cv2) — augmentations (blur, noise, rotation)
- Faker — synthetic data generation
- rich — CLI progress output

Install via:

    pip install pymupdf pillow opencv-python faker rich

---

## Project Structure

    formation_doc_generator/
    ├── templates/                    # Raw blank PDF templates (one per state)
    ├── field_maps/                   # Per-template field coordinate configs
    │   ├── ma_corp_articles.json
    │   ├── ny_corp_certificate.json
    │   └── (one per state)
    ├── fonts/                        # .ttf font files for text injection
    ├── output/
    │   ├── pdfs/                     # Filled PDFs
    │   ├── images/                   # PNG renders of each page
    │   └── ground_truth/             # JSON ground truth sidecar files
    ├── generator/
    │   ├── __init__.py
    │   ├── field_map.py              # Load and validate field coordinate configs
    │   ├── faker_data.py             # State-aware fake data generation
    │   ├── pdf_filler.py             # Inject text into PDF templates
    │   ├── renderer.py               # Render PDF pages to PNG images
    │   ├── augmentor.py              # Apply image augmentations
    │   └── ground_truth.py           # Write ground-truth JSON sidecars
    ├── tools/
    │   ├── inspect_template.py       # Grid overlay helper to find field bboxes
    │   └── validate_dataset.py       # Validate output completeness
    └── generate.py                   # CLI entry point

---

## Step 1: Field Coordinate Maps

For each template PDF, create a JSON config in `field_maps/` that defines where
each field lives. Use PyMuPDF's `page.get_text("dict")` and `page.rect` to
inspect the PDF and locate fields manually, then hardcode coordinates.

Each field map JSON must follow this schema:

    {
      "template": "ma_corp_articles.pdf",
      "state": "MA",
      "entity_type": "CORP",
      "fields": [
        {
          "field_id": "entity_name",
          "page": 0,
          "bbox": [x0, y0, x1, y1],
          "font_size": 11,
          "font_family": "variable",
          "multiline": false
        },
        {
          "field_id": "principal_office_street",
          "page": 0,
          "bbox": [x0, y0, x1, y1],
          "font_size": 10,
          "font_family": "variable",
          "multiline": false
        }
      ]
    }

`font_family: "variable"` means the generator should randomly pick a font at
runtime from the `fonts/` directory to simulate different typewriters/printers.

Write a helper script `tools/inspect_template.py` that accepts a PDF path and
renders each page with a numbered grid overlay to assist with manually identifying
field bounding boxes.

---

## Step 2: State-Aware Faker Data Generation (faker_data.py)

Use the `faker` library to generate realistic synthetic data. Data must be
geographically consistent with the state of the document (e.g. a Massachusetts
Articles of Organization should have a Massachusetts address, not a Texas one).

Generate the following fields for each document:

    @dataclass
    class FormationDocData:
        # -- CRM / Webform target fields (must match ground truth JSON schema) --
        entity_name: str            # e.g. "GREENFIELD LOGISTICS, INC."
        entity_type: str            # "CORP" | "LLC"
        state_of_formation: str     # Two-letter state code, e.g. "MA"
        principal_office_street: str
        principal_office_city: str
        principal_office_state: str
        principal_office_zip: str
        registered_agent_name: str
        registered_agent_street: str
        registered_agent_city: str
        registered_agent_state: str
        registered_agent_zip: str
        incorporator_name: str
        incorporator_address: str
        tax_id_number: str          # EIN format: XX-XXXXXXX
        formation_date: str         # MM/DD/YYYY
        authorized_shares: str      # Corporations only, e.g. "200 shares, no par value"
        business_purpose: str       # e.g. "any lawful purpose"

        # -- Document metadata (for file naming and audit) --
        doc_id: str                 # UUID
        template_name: str

Entity names should follow realistic corporate naming patterns:
- Corps: "[SURNAME] [INDUSTRY_WORD], INC." or "[TWO_WORDS] CORPORATION"
- LLCs: "[SURNAME] [SERVICE], LLC" or "[PLACE] [NOUN], LLC"
- Use Faker's `last_name()`, `company()`, `bs()` to build realistic names
- Force entity name to UPPERCASE to match typical formation doc formatting

Use `Faker('en_US')` with a seeded random state for reproducibility.

---

## Step 3: PDF Text Injection (pdf_filler.py)

Using PyMuPDF, overlay generated text onto the blank template PDF:

- Load the template PDF with `fitz.open()`
- For each field in the field map, use `page.insert_textbox()` to inject the
  generated value at the specified bbox
- Randomly select a font from the `fonts/` directory for `font_family: "variable"`
  fields. Include at least 3 font styles:
  - A clean sans-serif (simulates laser printer): e.g. Liberation Sans
  - A monospace (simulates typewriter): e.g. Courier Prime
  - A slightly informal sans (simulates inkjet): e.g. Open Sans
- Font size should jitter slightly: `font_size + random.uniform(-0.5, 0.5)`
- Text color should be near-black with slight variation: RGB values in range
  (5–20, 5–20, 5–20) to avoid perfectly pure black
- Save filled PDF to `output/pdfs/{doc_id}_{state}_{entity_type}.pdf`

---

## Step 4: PDF to Image Rendering (renderer.py)

Render each filled PDF page to a PNG image:

- Use `page.get_pixmap(dpi=200)` for base resolution
- Save each page as `output/images/{doc_id}_p{page_num}.png`
- Also save a thumbnail at 96 DPI for quick visual QA

---

## Step 5: Image Augmentations (augmentor.py)

Apply the following augmentations to produce additional document variants from
each base render. Each augmentation combination produces a new image AND a
corresponding copy of the ground-truth JSON (values are identical; only the
image changes).

Augmentation profiles:

    AUGMENTATION_PROFILES = {
        "clean":         {},
        "slight_scan":   {"rotation_deg": (-1.5, 1.5), "gaussian_noise_std": 3,  "blur_kernel": 0},
        "moderate_scan": {"rotation_deg": (-3, 3),      "gaussian_noise_std": 8,  "blur_kernel": 3},
        "heavy_scan":    {"rotation_deg": (-4, 4),      "gaussian_noise_std": 15, "blur_kernel": 5,
                          "jpeg_quality": 65},
        "fax":           {"rotation_deg": (-1, 1),      "gaussian_noise_std": 20, "blur_kernel": 1,
                          "jpeg_quality": 55, "contrast_factor": 1.3},
    }

Implementation details:

- **Rotation**: Use `cv2.getRotationMatrix2D` + `cv2.warpAffine`. Fill border with white (255, 255, 255).
- **Gaussian noise**: Generate noise array with `np.random.normal(0, std, img.shape)`, clip to [0, 255].
- **Blur**: Apply `cv2.GaussianBlur(img, (kernel, kernel), 0)` — only when kernel > 0.
- **JPEG compression artifact**: Save to BytesIO as JPEG at given quality, reload with PIL.
- **Contrast**: Use `PIL.ImageEnhance.Contrast(img).enhance(factor)`.

Each augmented image filename should encode the profile:

    {doc_id}_p{page_num}_{profile_name}.png

---

## Step 6: Ground Truth JSON (ground_truth.py)

For each generated document, write a sidecar JSON to `output/ground_truth/`:

    {
      "doc_id": "uuid-here",
      "template": "ma_corp_articles.pdf",
      "state_of_formation": "MA",
      "entity_type": "CORP",
      "images": [
        "output/images/uuid_p0_clean.png",
        "output/images/uuid_p0_slight_scan.png"
      ],
      "fields": {
        "entity_name":                "GREENFIELD LOGISTICS, INC.",
        "principal_office_street":    "142 BOYLSTON STREET",
        "principal_office_city":      "BOSTON",
        "principal_office_state":     "MA",
        "principal_office_zip":       "02116",
        "registered_agent_name":      "HAROLD T. VANCE",
        "registered_agent_street":    "88 CAMBRIDGE ST",
        "registered_agent_city":      "CAMBRIDGE",
        "registered_agent_state":     "MA",
        "registered_agent_zip":       "02139",
        "incorporator_name":          "DIANA L. COSTA",
        "incorporator_address":       "55 PARK ST, BOSTON, MA 02108",
        "tax_id_number":              "83-4521067",
        "formation_date":             "03/12/2024",
        "authorized_shares":          "200 shares, no par value",
        "business_purpose":           "any lawful purpose"
      },
      "azure_target_mapping": {
        "entity_name":             "Company",
        "principal_office_street": "Address",
        "tax_id_number":           "Tax Id Number",
        "state_of_formation":      "state_of_formation",
        "entity_type":             "entity_type"
      }
    }

The `azure_target_mapping` block explicitly maps each extracted field name to
the corresponding CRM webform field name, so the Azure Content Understanding
model's output can be validated against this ground truth.

---

## Step 7: CLI Entry Point (generate.py)

    Usage: python generate.py [OPTIONS]

    Options:
      --count INTEGER        Total number of documents to generate [default: 50]
      --seed INTEGER         Random seed for reproducibility [default: 42]
      --states TEXT          Comma-separated state codes [default: MA,NY,DE,TX,FL]
      --augmentations TEXT   Comma-separated augmentation profiles to apply
                             [default: clean,slight_scan,moderate_scan]
      --output-dir PATH      Output directory [default: ./output]
      --inspect TEMPLATE     Run the template inspector on a given PDF and exit
      --help                 Show this message and exit

The generator should:

1. Distribute `--count` documents evenly across the specified states
2. For each document, apply all specified augmentation profiles
3. Print a progress bar using `rich.progress`
4. On completion, print a summary table: docs generated per state, total images,
   total ground-truth files

---

## Step 8: Validation Script (tools/validate_dataset.py)

Write a script that:

1. Loads all ground-truth JSONs from `output/ground_truth/`
2. Checks that every image path referenced in each JSON actually exists on disk
3. Prints a per-state summary table: doc count, image count, any missing files
4. Prints field coverage: for each field name, what % of docs have a non-null value
5. Exits with code 1 if any referenced files are missing

---

## Additional Requirements

- All randomness must flow through a single `random.Random(seed)` instance passed
  throughout — no bare `random.random()` calls — so the full dataset is reproducible
  with the same seed.
- Include a `README.md` documenting: setup, how to add a new state template, how to
  update field coordinate maps, and how the azure_target_mapping works.
- Do not include any real PII — all data is Faker-generated.
- Font files (Liberation Sans, Courier Prime, Open Sans) must be downloaded separately
  from Google Fonts and placed in the `fonts/` directory. Document this in the README.
