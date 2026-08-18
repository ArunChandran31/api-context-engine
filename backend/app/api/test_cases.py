from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.dependencies import (
    AIDependencies,
    build_ai_dependencies,
)
from app.schemas.test_case import (
    TestCaseGenerationRequest,
    TestCaseGenerationResponse,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@lru_cache
def get_ai_dependencies() -> AIDependencies:
    return build_ai_dependencies()


@router.post(
    "/test-cases",
    response_model=TestCaseGenerationResponse,
)
def generate_test_cases(
    request: TestCaseGenerationRequest,
    dependencies: Annotated[
        AIDependencies,
        Depends(get_ai_dependencies),
    ],
) -> TestCaseGenerationResponse:
    result = dependencies.test_case_generation_service.generate(
        endpoint=request.question,
        specification_id=request.specification_id,
        test_style=request.test_style,
        categories=request.categories,
    )

    return TestCaseGenerationResponse(
        test_cases=result.test_cases,
    )
