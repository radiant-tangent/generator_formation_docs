"""Load and validate per-template field coordinate configurations."""

import json
import os
from typing import Any


class FieldMapError(Exception):
    """Raised when a field map is invalid."""


REQUIRED_FIELD_KEYS = {"field_id", "page", "bbox"}
REQUIRED_TOP_KEYS = {"template", "state", "entity_type", "fields"}


def load_field_map(path: str) -> dict[str, Any]:
    """Load a field map JSON and validate its structure.

    Args:
        path: Path to the field map JSON file.

    Returns:
        Validated field map dictionary.

    Raises:
        FieldMapError: If the field map is structurally invalid.
    """
    with open(path, "r") as f:
        data = json.load(f)

    missing_top = REQUIRED_TOP_KEYS - set(data.keys())
    if missing_top:
        raise FieldMapError(f"Missing top-level keys in {path}: {missing_top}")

    if not isinstance(data["fields"], list) or len(data["fields"]) == 0:
        raise FieldMapError(f"'fields' must be a non-empty list in {path}")

    for i, field in enumerate(data["fields"]):
        missing_field = REQUIRED_FIELD_KEYS - set(field.keys())
        if missing_field:
            raise FieldMapError(
                f"Field {i} ({field.get('field_id', '?')}) missing keys: {missing_field} in {path}"
            )

        bbox = field["bbox"]
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise FieldMapError(
                f"Field {i} ({field['field_id']}): bbox must be a 4-element list in {path}"
            )

        if not all(isinstance(c, (int, float)) for c in bbox):
            raise FieldMapError(
                f"Field {i} ({field['field_id']}): bbox elements must be numbers in {path}"
            )

        x0, y0, x1, y1 = bbox
        if x1 <= x0 or y1 <= y0:
            raise FieldMapError(
                f"Field {i} ({field['field_id']}): bbox has zero or negative area in {path}"
            )

    return data


def load_all_field_maps(field_maps_dir: str) -> dict[str, dict[str, Any]]:
    """Load all field map JSONs from a directory.

    Args:
        field_maps_dir: Directory containing field map JSON files.

    Returns:
        Dict keyed by state code (e.g. "MA") mapping to field map data.
    """
    maps = {}
    if not os.path.isdir(field_maps_dir):
        raise FieldMapError(f"Field maps directory not found: {field_maps_dir}")

    for fname in sorted(os.listdir(field_maps_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(field_maps_dir, fname)
        data = load_field_map(path)
        key = f"{data['state']}_{data['entity_type']}"
        maps[key] = data

    return maps


def get_field_map_for_state(
    field_maps: dict[str, dict[str, Any]],
    state: str,
    entity_type: str,
) -> dict[str, Any]:
    """Look up the field map for a given state/entity combination.

    Args:
        field_maps: All loaded field maps.
        state: Two-letter state code.
        entity_type: "CORP" or "LLC".

    Returns:
        The matching field map.

    Raises:
        FieldMapError: If no map exists for the given state/entity.
    """
    key = f"{state}_{entity_type}"
    if key not in field_maps:
        available = ", ".join(sorted(field_maps.keys()))
        raise FieldMapError(
            f"No field map for {key}. Available: {available}"
        )
    return field_maps[key]
