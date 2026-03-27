"""Template inspector: renders PDF pages with a numbered grid overlay to help identify field bounding boxes."""

import argparse
import os
import sys

import fitz  # PyMuPDF


def render_with_grid(
    pdf_path: str,
    output_dir: str,
    grid_spacing: int = 50,
    dpi: int = 150,
):
    """Render each page of a PDF with a coordinate grid overlay.

    Args:
        pdf_path: Path to the PDF template.
        output_dir: Directory to save annotated PNG images.
        grid_spacing: Grid line spacing in PDF points (1 pt = 1/72 inch).
        dpi: Resolution for rendering.
    """
    doc = fitz.open(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(pdf_path))[0]

    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect
        width = rect.width
        height = rect.height

        # Draw grid lines
        shape = page.new_shape()

        # Vertical lines
        x = 0
        while x <= width:
            shape.draw_line(fitz.Point(x, 0), fitz.Point(x, height))
            shape.finish(color=(1, 0, 0), width=0.3)
            # Label
            if x > 0:
                shape.insert_text(
                    fitz.Point(x + 1, 10),
                    str(int(x)),
                    fontsize=6,
                    color=(1, 0, 0),
                )
            x += grid_spacing

        # Horizontal lines
        y = 0
        while y <= height:
            shape.draw_line(fitz.Point(0, y), fitz.Point(width, y))
            shape.finish(color=(0, 0, 1), width=0.3)
            # Label
            if y > 0:
                shape.insert_text(
                    fitz.Point(1, y - 1),
                    str(int(y)),
                    fontsize=6,
                    color=(0, 0, 1),
                )
            y += grid_spacing

        shape.commit()

        # Render to PNG
        pix = page.get_pixmap(dpi=dpi)
        out_path = os.path.join(output_dir, f"{basename}_p{page_num}_grid.png")
        pix.save(out_path)
        print(f"Saved: {out_path} ({width:.0f} x {height:.0f} pts)")

    doc.close()


def inspect_text_blocks(pdf_path: str):
    """Print all text blocks found in the PDF with their bounding boxes."""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n--- Page {page_num} (size: {page.rect.width:.0f} x {page.rect.height:.0f} pts) ---")
        blocks = page.get_text("dict")["blocks"]
        for i, block in enumerate(blocks):
            if block["type"] == 0:  # Text block
                bbox = block["bbox"]
                lines_text = []
                for line in block["lines"]:
                    for span in line["spans"]:
                        lines_text.append(span["text"])
                text = " ".join(lines_text).strip()
                if text:
                    print(f"  Block {i}: bbox={[round(c, 1) for c in bbox]}  text={text!r}")
    doc.close()


def main():
    parser = argparse.ArgumentParser(
        description="Inspect a PDF template with grid overlay and text block detection."
    )
    parser.add_argument("pdf_path", help="Path to the PDF template file")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save grid-overlaid images (default: same dir as PDF)",
    )
    parser.add_argument(
        "--grid-spacing",
        type=int,
        default=50,
        help="Grid spacing in PDF points (default: 50)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Render resolution (default: 150)",
    )
    parser.add_argument(
        "--text-blocks",
        action="store_true",
        help="Also print detected text blocks with bounding boxes",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.pdf_path):
        print(f"Error: file not found: {args.pdf_path}", file=sys.stderr)
        return 1

    output_dir = args.output_dir or os.path.dirname(args.pdf_path) or "."

    render_with_grid(args.pdf_path, output_dir, args.grid_spacing, args.dpi)

    if args.text_blocks:
        inspect_text_blocks(args.pdf_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
