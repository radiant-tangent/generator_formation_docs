"""Validate the generated dataset for completeness and correctness."""

import json
import os
import sys
from collections import defaultdict

from rich.console import Console
from rich.table import Table

console = Console()


def main(output_dir: str = "./output"):
    gt_dir = os.path.join(output_dir, "ground_truth")

    if not os.path.isdir(gt_dir):
        console.print(f"[red]Error:[/red] Ground truth directory not found: {gt_dir}")
        return 1

    # Load all ground truth files
    gt_files = sorted(f for f in os.listdir(gt_dir) if f.endswith(".json"))
    if not gt_files:
        console.print(f"[red]Error:[/red] No ground truth JSON files found in {gt_dir}")
        return 1

    console.print(f"\nValidating {len(gt_files)} ground truth files in {gt_dir}\n")

    state_stats = defaultdict(lambda: {"docs": 0, "images": 0, "missing_images": []})
    field_presence = defaultdict(int)
    total_docs = 0
    total_missing = 0
    all_field_names = set()
    errors = []

    for gt_file in gt_files:
        gt_path = os.path.join(gt_dir, gt_file)
        try:
            with open(gt_path, "r") as f:
                gt = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {gt_file}: {e}")
            continue

        total_docs += 1
        state = gt.get("state_of_formation", "UNKNOWN")
        state_stats[state]["docs"] += 1

        # Check images exist
        images = gt.get("images", [])
        state_stats[state]["images"] += len(images)
        for img_path in images:
            if not os.path.isfile(img_path):
                # Also try relative to output_dir
                alt_path = os.path.join(output_dir, os.path.basename(img_path))
                if not os.path.isfile(alt_path):
                    state_stats[state]["missing_images"].append(img_path)
                    total_missing += 1

        # Track field coverage
        fields = gt.get("fields", {})
        for field_name, value in fields.items():
            all_field_names.add(field_name)
            if value is not None and value != "":
                field_presence[field_name] += 1

    # Print per-state summary
    state_table = Table(title="Per-State Summary")
    state_table.add_column("State", style="cyan")
    state_table.add_column("Documents", justify="right")
    state_table.add_column("Images", justify="right")
    state_table.add_column("Missing Images", justify="right", style="red")

    for state in sorted(state_stats.keys()):
        s = state_stats[state]
        missing_count = len(s["missing_images"])
        missing_style = "red" if missing_count > 0 else "green"
        state_table.add_row(
            state,
            str(s["docs"]),
            str(s["images"]),
            f"[{missing_style}]{missing_count}[/{missing_style}]",
        )

    console.print(state_table)

    # Print field coverage
    coverage_table = Table(title="Field Coverage")
    coverage_table.add_column("Field", style="cyan")
    coverage_table.add_column("Present", justify="right")
    coverage_table.add_column("Total", justify="right")
    coverage_table.add_column("Coverage %", justify="right")

    for field_name in sorted(all_field_names):
        present = field_presence.get(field_name, 0)
        pct = (present / total_docs * 100) if total_docs > 0 else 0
        style = "green" if pct >= 90 else ("yellow" if pct >= 50 else "red")
        coverage_table.add_row(
            field_name,
            str(present),
            str(total_docs),
            f"[{style}]{pct:.1f}%[/{style}]",
        )

    console.print(coverage_table)

    # Print errors
    if errors:
        console.print(f"\n[red]Errors ({len(errors)}):[/red]")
        for err in errors:
            console.print(f"  - {err}")

    # Print missing image details
    if total_missing > 0:
        console.print(f"\n[red]Missing images: {total_missing}[/red]")
        for state in sorted(state_stats.keys()):
            for img in state_stats[state]["missing_images"][:5]:
                console.print(f"  - [{state}] {img}")
            remaining = len(state_stats[state]["missing_images"]) - 5
            if remaining > 0:
                console.print(f"  ... and {remaining} more for {state}")

    # Summary
    console.print(f"\n[bold]Total documents:[/bold] {total_docs}")
    console.print(f"[bold]Total missing images:[/bold] {total_missing}")

    if total_missing > 0 or errors:
        console.print("\n[red bold]VALIDATION FAILED[/red bold]")
        return 1
    else:
        console.print("\n[green bold]VALIDATION PASSED[/green bold]")
        return 0


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./output"
    sys.exit(main(output_dir))
