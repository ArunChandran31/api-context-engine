from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.dependencies import AIDependencies
from app.ai.runtime import get_ai_dependencies
from app.core.auth import AuthenticatedUser, get_current_user
from app.database.session import get_db
from app.schemas.ai import (
    QuestionRequest,
    QuestionResponse,
    QuestionSource,
)
from app.services.api_specification_service import ApiSpecificationService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

specification_service = ApiSpecificationService()


@router.post(
    "/question",
    response_model=QuestionResponse,
)
def answer_question(
    request: QuestionRequest,
    db: Annotated[Session, Depends(get_db)],
    dependencies: Annotated[
        AIDependencies,
        Depends(get_ai_dependencies),
    ],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
) -> QuestionResponse:

    if not specification_service.belongs_to_user(
        db,
        request.specification_id,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API specification not found.",
        )

    result = dependencies.question_answering_service.answer(
        question=request.question,
        specification_id=request.specification_id,
    )

    return QuestionResponse(
        answer=result.answer.content,
        sources=[
            QuestionSource(
                specification_id=int(source.metadata["specification_id"]),
                endpoint_id=int(source.metadata["endpoint_id"]),
                method=str(source.metadata["method"]),
                path=str(source.metadata["path"]),
                operation_id=(
                    str(source.metadata["operation_id"])
                    if source.metadata.get("operation_id") is not None
                    else None
                ),
            )
            for source in result.sources
            if (
                "specification_id" in source.metadata
                and "endpoint_id" in source.metadata
                and "method" in source.metadata
                and "path" in source.metadata
            )
        ],
    )
