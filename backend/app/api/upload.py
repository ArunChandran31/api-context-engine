from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.exceptions import (
    EmptyUploadError,
    SpecificationAlreadyExistsError,
    SpecificationParseError,
    UnsupportedFileTypeError,
)
from app.rag.dependencies import get_rag_dependencies
from app.schemas.upload import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
)


def build_upload_service() -> UploadService:
    """
    Build the upload service with the application's
    shared RAG indexing orchestrator.
    """

    rag_dependencies = get_rag_dependencies()

    return UploadService(
        rag_indexing_orchestrator=rag_dependencies.indexing_orchestrator,
    )


upload_service = build_upload_service()

ALLOWED_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
}


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_specification(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Upload and ingest an OpenAPI JSON or YAML specification.
    """

    filename = file.filename

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    filename_lower = filename.lower()

    if not any(filename_lower.endswith(extension) for extension in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JSON, YAML, and YML files are supported.",
        )

    try:
        content = await file.read()

        return upload_service.upload(
            db=db,
            content=content,
            filename=filename,
        )

    except EmptyUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc

    except SpecificationParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except SpecificationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
