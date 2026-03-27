"""Visual debug tool: renders colored bounding boxes from a field map onto the template PDF."""

import json
import os
import sys

import fitz  # PyMuPDF

COLORS = [
    (1, 0, 0),      # red
    (0, 0, 1),      # blue
    (0, 0.6, 0),    # green
    (0.8, 0, 0.8),  # purple
    (1, 0.5, 0),    # orange
    (0, 0.6, 0.6),  # teal
    (0.6, 0.3, 0),  # brown
    (1, 0, 0.5),    # pink
    (0.4, 0.4, 0),  # olive
    (0, 0.3, 0.8),  # dark blue
]


def overlay_field_map(template_path: str, field_map_path: str, output_dir: str, dpi: int = 200):
    """Render template pages with colored field map rectangles overlaid."""
    with open(field_map_path, "r") as f:
        field_map = json.load(f)

    doc = fitz.open(template_path)
    os.makedirs(output_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(template_path))[0]

    for page_num in range(len(doc)):
        page = doc[page_num]
        shape = page.new_shape()

        # Draw each field's bbox
        field_idx = 0
        for field in field_map["fields"]:
            if field["page"] != page_num:
                continue

            color = COLORS[field_idx % len(COLORS)]
            bbox = field["bbox"]
            rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])

            # Draw filled rectangle with transparency (semi-transparent)
            shape.draw_rect(rect)
            shape.finish(color=color, fill=color, fill_opacity=0.2, width=1.5)

            # Label with field_id
            label = field["field_id"]
            label_pt = fitz.Point(bbox[0] + 2, bbox[1] + 8)
            shape.insert_text(label_pt, label, fontsize=6, color=color)

            field_idx += 1

        shape.commit()

        # Render
        pix = page.get_pixmap(dpi=dpi)
        out_path = os.path.join(output_dir, f"{basename}_p{page_num}_debug.png")
        pix.save(out_path)
        print(f"Saved: {out_path}")

    doc.close()


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/debug_field_map.py <template.pdf> <field_map.json> [output_dir]")
        return 1

    template_path = sys.argv[1]
    field_map_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "/tmp/debug_fields"

    if not os.path.isfile(template_path):
        print(f"Error: template not found: {template_path}")
        return 1
    if not os.path.isfile(field_map_path):
        print(f"Error: field map not found: {field_map_path}")
        return 1

    overlay_field_map(template_path, field_map_path, output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
