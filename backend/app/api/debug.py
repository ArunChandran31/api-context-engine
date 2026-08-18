from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.dependencies import (
    AIDependencies,
    build_ai_dependencies,
)
from app.schemas.debug import (
    DebugRequest,
    DebugResponse,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@lru_cache
def get_ai_dependencies() -> AIDependencies:
    return build_ai_dependencies()


@router.post(
    "/debug",
    response_model=DebugResponse,
)
def debug_endpoint(
    request: DebugRequest,
    dependencies: Annotated[
        AIDependencies,
        Depends(get_ai_dependencies),
    ],
) -> DebugResponse:
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
