from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.dependencies import AIDependencies
from app.ai.runtime import get_ai_dependencies
from app.core.auth import AuthenticatedUser, get_current_user
from app.database.session import get_db
from app.schemas.test_case import (
    TestCaseGenerationRequest,
    TestCaseGenerationResponse,
)
from app.services.api_specification_service import ApiSpecificationService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

specification_service = ApiSpecificationService()


@router.post(
    "/test-cases",
    response_model=TestCaseGenerationResponse,
)
def generate_test_cases(
    request: TestCaseGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
    dependencies: Annotated[
        AIDependencies,
        Depends(get_ai_dependencies),
    ],
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
) -> TestCaseGenerationResponse:

    if not specification_service.belongs_to_user(
        db,
        request.specification_id,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API specification not found.",
        )

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
