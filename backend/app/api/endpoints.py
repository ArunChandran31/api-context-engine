from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user
from app.database.session import get_db
from app.exceptions import EndpointAlreadyExistsError
from app.schemas.endpoint import (
    EndpointCreate,
    EndpointResponse,
)
from app.services.api_specification_service import ApiSpecificationService
from app.services.endpoint_service import EndpointService

router = APIRouter(
    prefix="/endpoints",
    tags=["Endpoints"],
)

service = EndpointService()
specification_service = ApiSpecificationService()


@router.post(
    "",
    response_model=EndpointResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_endpoint(
    endpoint: EndpointCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    if not specification_service.belongs_to_user(
        db,
        endpoint.api_specification_id,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API specification not found.",
        )

    try:
        return service.create(
            db,
            endpoint,
        )

    except EndpointAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/specification/{specification_id}",
    response_model=list[EndpointResponse],
)
def list_endpoints(
    specification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
):
    if not specification_service.belongs_to_user(
        db,
        specification_id,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API specification not found.",
        )

    return service.list_by_specification(
        db,
        specification_id,
    )
