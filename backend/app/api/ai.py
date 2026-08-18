from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.dependencies import AIDependencies, build_ai_dependencies
from app.schemas.ai import (
    QuestionRequest,
    QuestionResponse,
    QuestionSource,
)

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
