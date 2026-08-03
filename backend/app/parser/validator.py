from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml"}


def validate_file(file: UploadFile) -> None:
    if file.filename is None:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JSON and YAML files are supported.",
        )
