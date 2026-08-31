from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.dependencies import AIDependencies
from app.ai.runtime import get_ai_dependencies
from app.core.auth import AuthenticatedUser, get_current_user
from app.database.session import get_db
from app.schemas.debug import (
    DebugRequest,
    DebugResponse,
)
from app.services.api_specification_service import ApiSpecificationService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

specification_service = ApiSpecificationService()


@router.post(
    "/debug",
    response_model=DebugResponse,
)
def debug_endpoint(
    request: DebugRequest,
    db: Annotated[Session, Depends(get_db)],
    dependencies: Annotated[
        AIDependencies,
        Depends(get_ai_dependencies),
    ],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
) -> DebugResponse:

    if not specification_service.belongs_to_user(
        db,
        request.specification_id,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API specification not found.",
        )

    result = dependencies.debug_service.debug(
        question=request.question,
        specification_id=request.specification_id,
        endpoint=request.endpoint,
        status_code=request.status_code,
        error_message=request.error_message,
        request_body=request.request_body,
        response_body=request.response_body,
    )

    return DebugResponse(
        explanation=result.explanation,
    )
