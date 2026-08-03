import json

import yaml


def load_spec(contents: bytes) -> dict:
    """
    Load an OpenAPI specification from JSON or YAML.
    """
    text = contents.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)
