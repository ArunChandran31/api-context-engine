from pydantic import BaseModel, Field

from app.ai.test_case_models import GeneratedTestCase


class TestCaseGenerationRequest(BaseModel):
    __test__ = False
    question: str = Field(
        min_length=1,
    )


class TestCaseGenerationResponse(BaseModel):
    __test__ = False
    test_cases: list[GeneratedTestCase]
