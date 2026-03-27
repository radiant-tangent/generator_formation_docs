"""Write ground-truth JSON sidecar files for generated documents."""

import json
import os
from typing import Any

from generator.faker_data import FormationDocData

# Maps every extracted field to its CRM webform field name
AZURE_TARGET_MAPPING = {
    "entity_name": "Company",
    "entity_type": "Entity Type",
    "state_of_formation": "State of Formation",
    "principal_office_street": "Address",
    "principal_office_city": "City",
    "principal_office_state": "State",
    "principal_office_zip": "Zip Code",
    "registered_agent_name": "Registered Agent Name",
    "registered_agent_street": "Registered Agent Address",
    "registered_agent_city": "Registered Agent City",
    "registered_agent_state": "Registered Agent State",
    "registered_agent_zip": "Registered Agent Zip",
    "incorporator_name": "Incorporator Name",
    "incorporator_address": "Incorporator Address",
    "tax_id_number": "Tax Id Number",
    "formation_date": "Formation Date",
    "authorized_shares": "Authorized Shares",
    "business_purpose": "Business Purpose",
}


def write_ground_truth(
    doc_data: FormationDocData,
    image_paths: list[str],
    output_dir: str,
) -> str:
    """Write a ground-truth JSON sidecar for a generated document.

    Args:
        doc_data: The generated document data.
        image_paths: List of image file paths (all augmented variants).
        output_dir: Directory to write the JSON file.

    Returns:
        Path to the written JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)

    fields = doc_data.crm_fields()

    gt = {
        "doc_id": doc_data.doc_id,
        "template": doc_data.template_name,
        "state_of_formation": doc_data.state_of_formation,
        "entity_type": doc_data.entity_type,
        "images": image_paths,
        "fields": fields,
        "azure_target_mapping": AZURE_TARGET_MAPPING,
    }

    filename = f"{doc_data.doc_id}.json"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w") as f:
        json.dump(gt, f, indent=2)

    return output_path
