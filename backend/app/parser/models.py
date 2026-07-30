from pydantic import BaseModel


class Endpoint(BaseModel):
    path: str
    method: str
    summary: str | None = None

class ApiMetadata(BaseModel):
    title: str
    version: str
    endpoints: list[Endpoint]