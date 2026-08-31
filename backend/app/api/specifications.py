from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user
from app.database.session import get_db
from app.exceptions import (
    SpecificationAlreadyExistsError,
)
from app.schemas.api_specification import (
    ApiSpecificationCreate,
    ApiSpecificationResponse,
)
from app.services.api_specification_service import (
    ApiSpecificationService,
)

router = APIRouter(
    prefix="/specifications",
    tags=["API Specifications"],
)

service = ApiSpecificationService()


@router.post(
    "",
    response_model=ApiSpecificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_specification(
    specification: ApiSpecificationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    try:
        return service.create(
            db,
            specification,
            current_user,
        )

    except SpecificationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[ApiSpecificationResponse],
)
def list_specifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    return service.list(
        db,
        current_user,
    )


@router.get(
    "/{specification_id}",
    response_model=ApiSpecificationResponse,
)
def get_specification(
    specification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    specification = service.get(
        db,
        specification_id,
        current_user,
    )

    if specification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API specification with ID {specification_id} was not found.",
        )

    return specification
