from dataclasses import dataclass

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


@dataclass
class ParsedSpecification:
    title: str
    version: str | None
    description: str | None
    endpoints: list[ParsedEndpoint]
