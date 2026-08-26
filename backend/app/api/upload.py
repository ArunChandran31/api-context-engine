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
from app.rag.dependencies import RAGDependencies, get_rag_dependencies
from app.schemas.upload import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
)


def get_upload_service(
    rag_dependencies: RAGDependencies,
) -> UploadService:
    """
    Build the upload service from the application's
    shared RAG dependency graph.
    """

    return UploadService(
        rag_indexing_orchestrator=rag_dependencies.indexing_orchestrator,
    )


ALLOWED_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
}


def validate_filename(
    filename: str | None,
) -> str:
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

    return filename


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_specification(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    rag_dependencies: Annotated[
        RAGDependencies,
        Depends(get_rag_dependencies),
    ],
):
    """
    Upload and ingest an OpenAPI JSON or YAML specification.
    """

    upload_service = get_upload_service(
        rag_dependencies,
    )

    filename = validate_filename(
        file.filename,
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


@router.put(
    "/{specification_id}",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
)
async def replace_specification(
    specification_id: int,
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    rag_dependencies: Annotated[
        RAGDependencies,
        Depends(get_rag_dependencies),
    ],
):
    """
    Replace an existing OpenAPI specification and re-index it.
    """

    upload_service = get_upload_service(
        rag_dependencies,
    )

    filename = validate_filename(
        file.filename,
    )

    try:
        content = await file.read()

        return upload_service.replace(
            db=db,
            specification_id=specification_id,
            content=content,
            filename=filename,
        )

    except ValueError as exc:
        if "was not found" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise

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
