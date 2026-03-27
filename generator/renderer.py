"""Render filled PDF pages to PNG images using PyMuPDF."""

import os
from typing import Optional

import fitz  # PyMuPDF


def render_pdf_to_images(
    pdf_path: str,
    output_dir: str,
    doc_id: str,
    dpi: int = 200,
    thumbnail_dpi: int = 96,
) -> list[str]:
    """Render each page of a PDF to PNG images.

    Args:
        pdf_path: Path to the filled PDF.
        output_dir: Directory to save rendered images.
        doc_id: Document ID for filename prefix.
        dpi: Resolution for full-size renders.
        thumbnail_dpi: Resolution for thumbnail renders.

    Returns:
        List of paths to the rendered full-size PNG images.
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Full-size render
        pix = page.get_pixmap(dpi=dpi)
        img_filename = f"{doc_id}_p{page_num}.png"
        img_path = os.path.join(output_dir, img_filename)
        pix.save(img_path)
        image_paths.append(img_path)

        # Thumbnail render
        thumb_pix = page.get_pixmap(dpi=thumbnail_dpi)
        thumb_filename = f"{doc_id}_p{page_num}_thumb.png"
        thumb_path = os.path.join(output_dir, thumb_filename)
        thumb_pix.save(thumb_path)

    doc.close()
    return image_paths
