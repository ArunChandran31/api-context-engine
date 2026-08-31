from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class ApiSpecificationCreate(BaseSchema):
    title: str = Field(..., max_length=255)

    version: str | None = Field(default=None, max_length=50)

    description: str | None = None

    base_url: str | None = None

    source_file: str = Field(..., max_length=255)


class ApiSpecificationUpdate(BaseSchema):
    title: str | None = None

    version: str | None = None

    description: str | None = None


class ApiSpecificationResponse(TimestampSchema):
    id: int

    title: str

    version: str | None = None

    description: str | None

    base_url: str | None = None

    source_file: str
