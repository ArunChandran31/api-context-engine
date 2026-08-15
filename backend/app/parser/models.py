from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


class Endpoint(BaseModel):
    path: str
    method: str
    summary: str | None = None


class ApiMetadata(BaseModel):
    title: str
    version: str
    endpoints: list[Endpoint]


@dataclass
class ParsedEndpoint:
    path: str
    method: str
    summary: str | None = None
    description: str | None = None
    operation_id: str | None = None
    parameters: list[dict[str, Any]] | None = None
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] | None = None
    security: list[dict[str, Any]] | None = None


@dataclass
class ParsedSpecification:
    title: str
    version: str | None
    description: str | None
    endpoints: list[ParsedEndpoint]
