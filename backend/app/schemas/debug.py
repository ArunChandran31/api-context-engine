from pydantic import BaseModel, Field


class DebugRequest(BaseModel):
    question: str = Field(
        min_length=1,
    )


class DebugResponse(BaseModel):
    explanation: str
