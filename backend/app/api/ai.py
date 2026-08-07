from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.dependencies import AIDependencies, build_ai_dependencies
from app.schemas.ai import QuestionRequest, QuestionResponse

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@lru_cache
def get_ai_dependencies() -> AIDependencies:
    return build_ai_dependencies()


@router.post(
    "/question",
    response_model=QuestionResponse,
)
def answer_question(
    request: QuestionRequest,
    dependencies: Annotated[
        AIDependencies,
        Depends(get_ai_dependencies),
    ],
) -> QuestionResponse:
    result = dependencies.question_answering_service.answer(
        request.question,
    )

    return QuestionResponse(
        answer=result.content,
    )
