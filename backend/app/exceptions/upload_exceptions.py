from app.exceptions.api_exceptions import ApiContextEngineError


class UploadFailedError(ApiContextEngineError):
    """
    Raised when the upload workflow fails.
    """


class EmptyUploadError(ApiContextEngineError):
    """
    Raised when an empty file is uploaded.
    """
