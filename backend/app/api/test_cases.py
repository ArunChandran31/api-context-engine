from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.dependencies import AIDependencies
from app.ai.runtime import get_ai_dependencies
from app.schemas.test_case import (
    TestCaseGenerationRequest,
    TestCaseGenerationResponse,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


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
    try:
        result = dependencies.test_case_generation_service.generate(
            endpoint=request.question,
            specification_id=request.specification_id,
            test_style=request.test_style,
            categories=request.categories,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "Test case generation failed validation.",
                "message": str(exc),
            },
        ) from exc

    return TestCaseGenerationResponse(
        test_cases=result.test_cases,
        skipped_categories=result.skipped_categories,
    )
