from app.exceptions.api_exceptions import ApiContextEngineError


class InvalidSpecificationError(ApiContextEngineError):
    """
    Raised when an uploaded file is not a valid OpenAPI specification.
    """


class UnsupportedFileTypeError(ApiContextEngineError):
    """
    Raised when an unsupported file type is uploaded.
    """


class SpecificationParseError(ApiContextEngineError):
    """
    Raised when parsing fails.
    """
