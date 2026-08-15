from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class EndpointCreate(BaseSchema):
    api_specification_id: int

    path: str = Field(..., max_length=255)

    method: str = Field(..., max_length=10)

    summary: str | None = None

    description: str | None = None

    operation_id: str | None = None

    parameters: list[dict[str, Any]] | None = None

    request_body: dict[str, Any] | None = None

    responses: dict[str, Any] | None = None

    security: list[dict[str, Any]] | None = None


class EndpointResponse(BaseSchema):
    id: int

    api_specification_id: int

    path: str

    method: str

    summary: str | None

    description: str | None

    operation_id: str | None

    parameters: list[dict[str, Any]] | None

    request_body: dict[str, Any] | None

    responses: dict[str, Any] | None

    security: list[dict[str, Any]] | None
