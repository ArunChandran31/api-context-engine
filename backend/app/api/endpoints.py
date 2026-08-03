from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.exceptions import EndpointAlreadyExistsError
from app.schemas.endpoint import (
    EndpointCreate,
    EndpointResponse,
)
from app.services.endpoint_service import EndpointService

router = APIRouter(
    prefix="/endpoints",
    tags=["Endpoints"],
)

service = EndpointService()


@router.post(
    "",
    response_model=EndpointResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_endpoint(
    endpoint: EndpointCreate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return service.create(db, endpoint)
    except EndpointAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/specification/{specification_id}",
    response_model=list[EndpointResponse],
)
def list_endpoints(specification_id: int, db: Annotated[Session, Depends(get_db)]):
    return service.list_by_specification(
        db,
        specification_id,
    )
