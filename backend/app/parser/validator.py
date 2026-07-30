from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml"}
def validate_file(file: UploadFile):
    if not any(file.filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Only JSON and YAML files are supported."
        )