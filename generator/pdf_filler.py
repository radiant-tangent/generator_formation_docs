"""Inject generated text onto blank PDF templates using PyMuPDF."""

import math
import os
import random
from typing import Any

import fitz  # PyMuPDF

from generator.faker_data import FormationDocData


def _pick_font(fonts_dir: str, rng: random.Random) -> str:
    """Pick a random .ttf font from the fonts directory."""
    fonts = [f for f in os.listdir(fonts_dir) if f.lower().endswith((".ttf", ".otf"))]
    if not fonts:
        raise FileNotFoundError(f"No font files found in {fonts_dir}")
    return os.path.join(fonts_dir, rng.choice(fonts))


def _near_black_color(rng: random.Random) -> tuple[float, float, float]:
    """Generate a near-black color with slight variation (RGB 0-1 scale for PyMuPDF)."""
    r = rng.randint(5, 20) / 255.0
    g = rng.randint(5, 20) / 255.0
    b = rng.randint(5, 20) / 255.0
    return (r, g, b)


def _jittered_rect(rect: fitz.Rect, rng: random.Random) -> fitz.Rect:
    """Apply small positional jitter to a rectangle to simulate imperfect alignment."""
    dx = rng.uniform(-1.5, 1.5)
    dy = rng.uniform(-1.0, 1.0)
    return fitz.Rect(rect.x0 + dx, rect.y0 + dy, rect.x1 + dx, rect.y1 + dy)


def _rotation_morph(rect: fitz.Rect, rng: random.Random) -> tuple[fitz.Point, fitz.Matrix] | None:
    """Create a slight rotation morph to simulate non-perfectly-horizontal typing."""
    angle = rng.uniform(-0.6, 0.6)
    if abs(angle) < 0.05:
        return None
    center = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
    return (center, fitz.Matrix(angle))


def _fill_style(rng: random.Random) -> dict:
    """Pick random fill style parameters to simulate different ink/printer weights."""
    fill_opacity = rng.uniform(0.85, 1.0)
    return {"fill_opacity": fill_opacity}


def _typewriter_insert(
    page: fitz.Page,
    rect: fitz.Rect,
    text: str,
    fontname: str,
    fontfile: str,
    fontsize: float,
    color: tuple[float, float, float],
    rng: random.Random,
    style: dict,
) -> bool:
    """Insert text character by character with slight baseline wobble.

    Simulates a typewriter or dot-matrix printer where each character
    may sit slightly higher or lower on the baseline.

    Returns True if text was placed successfully (fits horizontally).
    """
    page.insert_font(fontname=fontname, fontfile=fontfile)
    font = fitz.Font(fontfile=fontfile)

    x = rect.x0
    # Vertically center the text in the rect
    y_base = rect.y0 + fontsize * 0.85

    for ch in text:
        if ch == " ":
            # Use measured space width + slight jitter
            space_w = font.char_lengths(" ", fontsize=fontsize)[0]
            x += space_w + rng.uniform(-0.2, 0.2)
            continue

        # Per-character baseline wobble: ±0.4pt
        dy = rng.uniform(-0.4, 0.4)
        # Per-character horizontal spacing jitter: ±0.15pt
        dx = rng.uniform(-0.15, 0.15)

        point = fitz.Point(x + dx, y_base + dy)
        if point.x > rect.x1:
            return False  # text doesn't fit

        page.insert_text(
            point,
            ch,
            fontname=fontname,
            fontfile=fontfile,
            fontsize=fontsize,
            color=color,
            fill_opacity=style.get("fill_opacity", 1.0),
            render_mode=style.get("render_mode", 0),
            border_width=style.get("border_width", 0),
        )

        # Advance by actual character width + small jitter
        char_w = font.char_lengths(ch, fontsize=fontsize)[0]
        x += char_w + rng.uniform(-0.15, 0.15)

    return True


def fill_pdf(
    template_path: str,
    field_map: dict[str, Any],
    doc_data: FormationDocData,
    fonts_dir: str,
    output_path: str,
    rng: random.Random,
) -> str:
    """Fill a PDF template with generated data.

    Args:
        template_path: Path to the blank PDF template.
        field_map: Field map dictionary with field coordinates.
        doc_data: Generated document data.
        fonts_dir: Directory containing .ttf font files.
        output_path: Path to save the filled PDF.
        rng: Seeded random instance.

    Returns:
        Path to the saved filled PDF.
    """
    doc = fitz.open(template_path)
    data_dict = doc_data.to_dict()

    # Register fonts - pick one per document for consistency within a doc,
    # but vary across documents
    font_path = _pick_font(fonts_dir, rng)
    font_name = os.path.splitext(os.path.basename(font_path))[0]

    # Decide per-document fill strategy: ~25% use typewriter mode
    use_typewriter = rng.random() < 0.25

    # Pick one ink color and fill style for the whole document
    doc_color = _near_black_color(rng)
    doc_style = _fill_style(rng)

    for field_def in field_map["fields"]:
        field_id = field_def["field_id"]
        value = data_dict.get(field_id, "")
        if not value:
            continue

        page_num = field_def["page"]
        if page_num >= len(doc):
            continue

        page = doc[page_num]
        bbox = field_def["bbox"]
        rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])

        base_font_size = field_def.get("font_size", 10)
        font_size = base_font_size + rng.uniform(-0.5, 0.5)
        font_size = max(6, font_size)  # Floor at 6pt

        color = doc_color

        # Use the document-level font; "variable" means it varies across
        # documents, not across fields within the same document.
        field_font_path = font_path

        field_font_name = os.path.splitext(os.path.basename(field_font_path))[0]

        # Register the font on this page
        page.insert_font(fontname=field_font_name, fontfile=field_font_path)

        # Apply realism: positional jitter and fill style
        jittered = _jittered_rect(rect, rng)
        style = doc_style
        morph = _rotation_morph(rect, rng)

        multiline = field_def.get("multiline", False)
        align = fitz.TEXT_ALIGN_LEFT

        # Typewriter mode: char-by-char with baseline wobble (single-line only)
        if use_typewriter and not multiline:
            ok = _typewriter_insert(
                page, jittered, value,
                field_font_name, field_font_path,
                font_size, color, rng, style,
            )
            if ok:
                continue
            # Fall through to textbox if typewriter didn't fit

        # Standard textbox insertion with jitter, rotation, and style
        rc = page.insert_textbox(
            jittered,
            value,
            fontname=field_font_name,
            fontfile=field_font_path,
            fontsize=font_size,
            color=color,
            align=align,
            morph=morph,
            **style,
        )

        # If text overflows (rc < 0), try with smaller font
        if rc < 0:
            for reduction in [1, 2, 3, 4]:
                smaller = font_size - reduction
                if smaller < 5:
                    break
                rc = page.insert_textbox(
                    jittered,
                    value,
                    fontname=field_font_name,
                    fontfile=field_font_path,
                    fontsize=smaller,
                    color=color,
                    align=align,
                    morph=morph,
                    **style,
                )
                if rc >= 0:
                    break

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()

    return output_path
