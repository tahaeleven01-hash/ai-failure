"""
Export JSON Schema for FailureCase model.
"""

import json
import sys
from pathlib import Path

# Add packages to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "packages"))

from afm.models import FailureCase


def main() -> None:
    schema = FailureCase.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "AIFailureCase"
    schema["description"] = "Schema for AI Failure Museum (AFM) failure definitions."

    output_dir = root_dir / "schemas"
    output_dir.mkdir(parents=True, exist_ok=True)
    schema_path = output_dir / "failure-case.schema.json"

    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"Schema successfully generated at: {schema_path}")


if __name__ == "__main__":
    main()
