"""CLI entry point for the formation document generator."""

import argparse
import os
import sys

import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from generator.field_map import load_all_field_maps, get_field_map_for_state
from generator.faker_data import FormationDataGenerator, FORM_TEMPLATE_MAP
from generator.pdf_filler import fill_pdf
from generator.renderer import render_pdf_to_images, images_to_pdf
from generator.augmentor import augment_image, AUGMENTATION_PROFILES
from generator.ground_truth import write_ground_truth

console = Console()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate synthetic company formation documents with ground-truth JSON."
    )
    parser.add_argument(
        "--count", type=int, default=50,
        help="Number of documents to generate per state (default: 50)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--states", type=str, default="MA_CORP,NY_CORP,NY_LLC,DE_LLC,TX_LLC,FL_CORP,MO_LLC,KS_CORP,CA_LLC",
        help="Comma-separated state_entity keys, e.g. MA_CORP,NY_LLC,CA_LLC (default: all)",
    )
    parser.add_argument(
        "--augmentations", type=str, default="slight_scan,moderate_scan",
        help="Comma-separated augmentation profiles (default: slight_scan,moderate_scan)",
    )
    parser.add_argument(
        "--output-dir", type=str, default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--template-set", type=str, default="no_fluff",
        choices=["no_fluff", "full"],
        help="Template set to use: 'no_fluff' (formation pages only) or 'full' (with instructions/cover pages). Default: no_fluff",
    )
    parser.add_argument(
        "--inspect", type=str, metavar="TEMPLATE",
        help="Run the template inspector on a given PDF and exit",
    )
    return parser.parse_args()


def run_inspector(template_path: str):
    """Run the template inspector and exit."""
    from tools.inspect_template import render_with_grid, inspect_text_blocks
    output_dir = os.path.dirname(template_path) or "."
    render_with_grid(template_path, output_dir)
    inspect_text_blocks(template_path)



def main():
    args = parse_args()

    # Handle --inspect mode
    if args.inspect:
        if not os.path.isfile(args.inspect):
            console.print(f"[red]Error:[/red] Template not found: {args.inspect}")
            return 1
        run_inspector(args.inspect)
        return 0

    # Parse arguments
    state_keys = [s.strip().upper() for s in args.states.split(",")]
    aug_profiles = [a.strip() for a in args.augmentations.split(",")]

    # Validate state keys
    for key in state_keys:
        if key not in FORM_TEMPLATE_MAP:
            console.print(f"[red]Error:[/red] Unknown state key: {key}")
            console.print(f"Available: {', '.join(FORM_TEMPLATE_MAP.keys())}")
            return 1

    # Validate augmentation profiles
    for profile in aug_profiles:
        if profile not in AUGMENTATION_PROFILES:
            console.print(f"[red]Error:[/red] Unknown augmentation profile: {profile}")
            console.print(f"Available: {', '.join(AUGMENTATION_PROFILES.keys())}")
            return 1

    # Base paths per doc_type are resolved per state_key in the loop below
    templates_base = os.path.join(PROJECT_ROOT, "templates")
    field_maps_base = os.path.join(PROJECT_ROOT, "field_maps")
    fonts_dir = os.path.join(PROJECT_ROOT, "fonts")
    pdfs_dir = os.path.join(args.output_dir, "pdfs")
    images_dir = os.path.join(args.output_dir, "images")
    gt_dir = os.path.join(args.output_dir, "ground_truth")

    # Verify prerequisites (check default formation_docs dir exists)
    default_templates_dir = os.path.join(templates_base, "formation_docs", args.template_set)
    if not os.path.isdir(default_templates_dir):
        console.print(f"[red]Error:[/red] Templates directory not found: {default_templates_dir}")
        console.print("Place PDF templates in templates/ first.")
        return 1

    if not os.path.isdir(fonts_dir) or not any(
        f.endswith((".ttf", ".otf")) for f in os.listdir(fonts_dir)
    ):
        console.print(f"[red]Error:[/red] No fonts found in {fonts_dir}")
        console.print("Run: python tools/download_fonts.py")
        return 1

    # Load field maps from all doc_type directories used by requested state_keys
    field_maps = {}
    doc_types_needed = {FORM_TEMPLATE_MAP[k]["doc_type"] for k in state_keys}
    for doc_type in doc_types_needed:
        fm_dir = os.path.join(field_maps_base, doc_type, args.template_set)
        if os.path.isdir(fm_dir):
            try:
                field_maps.update(load_all_field_maps(fm_dir))
            except Exception as e:
                console.print(f"[red]Error loading field maps from {fm_dir}:[/red] {e}")
                return 1

    # Create output directories
    for d in [pdfs_dir, images_dir, gt_dir]:
        os.makedirs(d, exist_ok=True)

    # Initialize generators with seeded RNGs (Option A)
    seed = args.seed
    data_gen = FormationDataGenerator(seed=seed)
    np_rng = np.random.default_rng(seed + 1)

    # Each state key gets --count documents
    state_counts = {key: args.count for key in state_keys}

    # Tracking stats
    stats = {key: {"docs": 0, "images": 0, "gt_files": 0} for key in state_keys}
    total_docs = args.count * len(state_keys)
    total_images = 0
    total_gt = 0

    console.print(f"\n[bold]Formation Document Generator[/bold]")
    console.print(f"  Documents: {args.count} per state/entity ({total_docs} total)")
    console.print(f"  States: {', '.join(state_keys)}")
    console.print(f"  Augmentations: {', '.join(aug_profiles)}")
    console.print(f"  Seed: {args.seed}")
    console.print(f"  Output: {args.output_dir}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generating documents...", total=total_docs)

        for state_key in state_keys:
            count = state_counts[state_key]
            config = FORM_TEMPLATE_MAP[state_key]
            state = config["state"]
            templates_dir = os.path.join(templates_base, config["doc_type"], args.template_set)
            template_path = os.path.join(templates_dir, config["template"])

            if not os.path.isfile(template_path):
                console.print(f"[yellow]Warning:[/yellow] Template not found: {template_path}, skipping {state_key}")
                progress.advance(task, count)
                continue

            try:
                fm = get_field_map_for_state(field_maps, state, config["entity_type"])
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] {e}, skipping {state_key}")
                progress.advance(task, count)
                continue

            for _i in range(count):
                # Generate data
                doc_data = data_gen.generate(state_key)

                # Fill PDF
                pdf_filename = f"{doc_data.doc_id}_{state}_{config['entity_type']}.pdf"
                pdf_path = os.path.join(pdfs_dir, pdf_filename)
                fill_pdf(template_path, fm, doc_data, fonts_dir, pdf_path, data_gen.rng)

                # Render to images
                base_images = render_pdf_to_images(pdf_path, images_dir, doc_data.doc_id)

                # Apply augmentations and assemble augmented PDFs
                all_image_paths = []
                # Collect augmented page paths grouped by profile
                profile_pages: dict[str, list[str]] = {p: [] for p in aug_profiles}
                for base_img in base_images:
                    page_stem = os.path.splitext(os.path.basename(base_img))[0]
                    for profile_name in aug_profiles:
                        aug_filename = f"{page_stem}_{profile_name}.png"
                        aug_path = os.path.join(images_dir, aug_filename)
                        augment_image(base_img, aug_path, profile_name, np_rng)
                        all_image_paths.append(aug_path)
                        profile_pages[profile_name].append(aug_path)

                # Create one PDF per augmentation profile
                for profile_name, pages in profile_pages.items():
                    if pages:
                        aug_pdf_name = f"{doc_data.doc_id}_{state}_{config['entity_type']}_{profile_name}.pdf"
                        aug_pdf_path = os.path.join(pdfs_dir, aug_pdf_name)
                        images_to_pdf(pages, aug_pdf_path)

                total_images += len(all_image_paths)

                # Write ground truth
                gt_path = write_ground_truth(doc_data, all_image_paths, gt_dir)
                total_gt += 1

                # Update stats
                stats[state_key]["docs"] += 1
                stats[state_key]["images"] += len(all_image_paths)
                stats[state_key]["gt_files"] += 1

                progress.advance(task)

    # Print summary
    console.print("\n[bold green]Generation complete![/bold green]\n")

    table = Table(title="Summary")
    table.add_column("State/Entity", style="cyan")
    table.add_column("Documents", justify="right")
    table.add_column("Images", justify="right")
    table.add_column("Ground Truth", justify="right")

    for key in state_keys:
        s = stats[key]
        table.add_row(key, str(s["docs"]), str(s["images"]), str(s["gt_files"]))

    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{sum(s['docs'] for s in stats.values())}[/bold]",
        f"[bold]{total_images}[/bold]",
        f"[bold]{total_gt}[/bold]",
    )
    console.print(table)

    return 0


if __name__ == "__main__":
    sys.exit(main())
