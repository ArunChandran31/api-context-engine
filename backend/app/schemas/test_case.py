from pydantic import BaseModel, Field

from app.ai.test_case_models import GeneratedTestCase


class TestCaseGenerationRequest(BaseModel):
    question: str = Field(
        min_length=1,
    )


class TestCaseGenerationResponse(BaseModel):
    test_cases: list[GeneratedTestCase]
