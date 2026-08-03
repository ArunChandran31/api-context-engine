import json
from pathlib import Path

import yaml


def load_specification(file_path: str) -> dict:
    """
    Load an OpenAPI specification from a JSON or YAML file.
    """

    extension = Path(file_path).suffix.lower()

    with open(file_path, "r", encoding="utf-8") as file:

        if extension == ".json":
            return json.load(file)

        if extension in {".yaml", ".yml"}:
            return yaml.safe_load(file)

    raise ValueError(f"Unsupported file type: {extension}")
