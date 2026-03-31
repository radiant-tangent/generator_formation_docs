---
title: Formation Document Generator
description: Python CLI pipeline for generating synthetic company formation documents with ground-truth JSON for Azure Content Understanding training.
---

## Overview

This project generates a synthetic dataset of realistic US company formation documents
(filled PDFs, rendered images, and ground-truth JSON files) for training and testing
an Azure Content Understanding model. The ground-truth schema maps directly to CRM
webform fields.

## Supported States

| State         | Entity Type | Document Name              | Template File            |
|---------------|-------------|----------------------------|--------------------------|
| Massachusetts | Corp        | Articles of Organization   | ma_corp_articles.pdf     |
| New York      | Corp        | Certificate of Incorporation | ny_corp_certificate.pdf |
| New York      | LLC         | Articles of Organization   | ny_llc_articles.pdf      |
| Delaware      | LLC         | Certificate of Formation   | de_llc_certificate.pdf   |
| Texas         | LLC         | Certificate of Formation   | tx_llc_certificate.pdf   |
| Florida       | Corp        | Articles of Incorporation  | fl_corp_articles.pdf     |
| Missouri      | LLC         | Articles of Organization   | mo_llc_articles.pdf      |
| Kansas        | Corp        | Articles of Incorporation  | ks_corp_articles.pdf     |
| California    | LLC         | Articles of Organization   | ca_llc_articles.pdf      |

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Download Fonts

The generator requires TTF font files for text injection. Run the download script:

```bash
python tools/download_fonts.py
```

This downloads Liberation Sans, Courier Prime, and Open Sans into `fonts/`.
If automatic download fails, manually download from:

- [Liberation Sans](https://github.com/liberationfonts/liberation-fonts/releases)
- [Courier Prime](https://fonts.google.com/specimen/Courier+Prime)
- [Open Sans](https://fonts.google.com/specimen/Open+Sans)

Place the `.ttf` files in the `fonts/` directory.

## Usage

### Generate Documents

```bash
python generate.py [OPTIONS]
```

**Options:**

| Option            | Default                              | Description                            |
|-------------------|--------------------------------------|----------------------------------------|
| `--count`         | 50                                   | Documents to generate per state/entity |
| `--seed`          | 42                                   | Random seed for reproducibility        |
| `--states`        | MA_CORP,NY_CORP,NY_LLC,DE_LLC,TX_LLC,FL_CORP,MO_LLC,KS_CORP,CA_LLC | Comma-separated state_entity keys |
| `--augmentations` | slight_scan,moderate_scan            | Comma-separated augmentation profiles  |
| `--output-dir`    | ./output                             | Output directory                       |
| `--template-set`  | no_fluff                             | Template set: `no_fluff` or `full`     |
| `--inspect`       |                                      | Run template inspector on a PDF        |

**Examples:**

```bash
# Generate 50 docs across all states (default)
python generate.py

# Generate 10 docs for MA Corp and NY LLC only, with all augmentations
python generate.py --count 10 --states MA_CORP,NY_LLC --augmentations slight_scan,moderate_scan,heavy_scan,fax

# Reproducible run with a specific seed
python generate.py --count 100 --seed 123
```

### Inspect a Template

Use the inspector to view PDF templates with a coordinate grid overlay:

```bash
python tools/inspect_template.py templates/ma_corp_articles.pdf --text-blocks
```

### Validate Output

Check that all generated images and ground-truth files are consistent:

```bash
python tools/validate_dataset.py ./output
```

## Project Structure

```text
formation_doc_generator/
├── templates/            # Real blank PDF templates from state agencies
├── field_maps/           # Per-template field coordinate configs (JSON)
├── fonts/                # TTF font files for text injection
├── output/
│   ├── pdfs/             # Base filled PDFs + augmented PDFs per profile
│   ├── images/           # PNG renders (base + augmented)
│   └── ground_truth/     # JSON ground-truth sidecar files
├── generator/
│   ├── field_map.py      # Load and validate field coordinate configs
│   ├── faker_data.py     # State-aware fake data generation
│   ├── pdf_filler.py     # Inject text into PDF templates
│   ├── renderer.py       # Render PDF pages to PNG images
│   ├── augmentor.py      # Apply image augmentations
│   └── ground_truth.py   # Write ground-truth JSON sidecars
├── tools/
│   ├── inspect_template.py    # Grid overlay helper for field bboxes
│   ├── validate_dataset.py    # Validate output completeness
│   └── download_fonts.py      # Download required font files
├── generate.py           # CLI entry point
└── requirements.txt
```

## Adding a New State Template

1. Download the blank PDF form from the states filing agency website
2. Place it in `templates/` with the naming convention `{state}_{entity_type}_{doctype}.pdf`
3. Run the inspector to identify field positions:

   ```bash
   python tools/inspect_template.py templates/your_template.pdf --text-blocks
   ```

4. Create a field map JSON in `field_maps/` matching the template name:

   ```json
   {
     "template": "your_template.pdf",
     "state": "XX",
     "entity_type": "CORP",
     "fields": [
       {
         "field_id": "entity_name",
         "page": 0,
         "bbox": [x0, y0, x1, y1],
         "font_size": 11,
         "font_family": "variable",
         "multiline": false
       }
     ]
   }
   ```

5. Add the state to `STATE_CONFIG` and `STATE_TEMPLATE_MAP` in `generator/faker_data.py`
6. Run a test generation: `python generate.py --count 1 --states XX`

## Updating Field Coordinate Maps

Field coordinates use PDF points (1 pt = 1/72 inch) with origin at top-left.
The `bbox` is `[x0, y0, x1, y1]` where (x0, y0) is top-left and (x1, y1) is
bottom-right of the text insertion area.

Use the grid overlay images from `inspect_template.py` to identify coordinates.
Red vertical lines show X positions; blue horizontal lines show Y positions.

## Azure Target Mapping

Each ground-truth JSON includes an `azure_target_mapping` block that maps extracted
field names to CRM webform field names:

```json
{
  "azure_target_mapping": {
    "entity_name": "Company",
    "entity_type": "Entity Type",
    "state_of_formation": "State of Formation",
    "principal_office_street": "Address",
    "principal_office_city": "City",
    "tax_id_number": "Tax Id Number"
  }
}
```

This mapping enables validation of the Azure Content Understanding models output
against the ground truth, ensuring the extracted values land in the correct CRM fields.

## Augmentation Profiles

Each augmentation profile applies a combination of page-level transforms to
simulate real-world scan, fax, and copy artifacts. Every document produces a
base PDF (filled, no augmentation) plus one augmented PDF and image set per
requested profile.

| Profile        | Rotation | Noise | Blur | JPEG | Contrast | Perspective | Shadow | Tint | Brightness | Margin | Speckle | Vignette |
|----------------|----------|-------|------|------|----------|-------------|--------|------|------------|--------|---------|----------|
| slight_scan    | ±1.5°    | σ=3   | —    | —    | —        | —           | —      | 2-6% | ±10        | ±8 px  | —       | —        |
| moderate_scan  | ±3°      | σ=8   | k=1  | —    | —        | 0.2-0.6%    | 15-30  | 3-8% | ±15        | ±15 px | 0.05%   | —        |
| heavy_scan     | ±4°      | σ=15  | k=5  | 65   | —        | 0.5-1.2%    | 25-50  | 5-12%| ±25        | ±20 px | 0.2%    | 30-60%   |
| fax            | ±1°      | σ=20  | k=1  | 55   | 1.3×     | 0.2-0.5%    | 10-25  | 6-15%| ±20        | —      | 0.3%    | 20-50%   |

**Effect descriptions:**

| Effect      | Simulates                                           |
|-------------|-----------------------------------------------------|
| Rotation    | Page skew from scanner placement                    |
| Noise       | Sensor noise from scanning hardware                 |
| Blur        | Focus degradation from scan/fax                     |
| JPEG        | Compression artifacts from digital transmission     |
| Contrast    | Over-exposed copies or fax contrast boost           |
| Perspective | Page not lying flat on scanner glass                |
| Shadow      | Dark edge shadows from flatbed scanner lid          |
| Tint        | Aged or off-white paper color                       |
| Brightness  | Variable scanner exposure across documents          |
| Margin      | Page placement offset on scanner glass              |
| Speckle     | Dust and dirt (salt-and-pepper noise)               |
| Vignette    | Light falloff toward corners from scanner optics    |

## Reproducibility

All randomness flows through seeded RNG instances derived from the `--seed` value:

- `random.Random(seed)` — font selection, color jitter, data distribution
- `Faker.seed_instance(seed)` — synthetic name/address generation
- `np.random.default_rng(seed + 1)` — image augmentation noise/rotation

Running with the same seed produces identical output.

## Data Safety

All generated data is synthetic (Faker-produced). No real PII is included in any output.
