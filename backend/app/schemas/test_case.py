from typing import Literal

from pydantic import BaseModel, Field

from app.ai.test_case_models import GeneratedTestCase

TestStyle = Literal[
    "jest",
    "pytest",
    "postman",
    "curl",
]

TestCategory = Literal[
    "happy",
    "validation",
    "edge",
    "auth",
    "other",
]


class TestCaseGenerationRequest(BaseModel):
    __test__ = False

    question: str = Field(
        min_length=1,
        description="Endpoint or natural-language test case request.",
    )

    specification_id: int = Field(
        gt=0,
        description="ID of the API specification to use as test-case context.",
    )

    test_style: TestStyle = Field(
        default="jest",
        description="Target format for generated test cases.",
    )

    categories: list[TestCategory] = Field(
        default_factory=lambda: [
            "happy",
            "validation",
            "edge",
            "auth",
            "other",
        ],
        description="Categories of test cases to generate.",
    )


class TestCaseGenerationResponse(BaseModel):
    __test__ = False

    test_cases: list[GeneratedTestCase]
