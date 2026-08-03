from pydantic import BaseModel


class UploadResponse(BaseModel):
    """
    Response returned after successfully ingesting
    an OpenAPI specification.
    """

    specification_id: int
    title: str
    version: str | None = None
    endpoints_created: int
    filename: str
