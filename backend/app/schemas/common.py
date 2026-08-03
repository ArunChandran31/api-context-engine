from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema for all API schemas.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class TimestampSchema(BaseSchema):
    """
    Shared timestamp fields.
    """

    created_at: datetime
