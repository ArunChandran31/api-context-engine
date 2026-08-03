class ApiContextEngineError(Exception):
    """
    Base exception for the API Context Engine.
    """


class SpecificationAlreadyExistsError(ApiContextEngineError):
    """
    Raised when an API specification already exists.
    """


class SpecificationNotFoundError(ApiContextEngineError):
    """
    Raised when an API specification cannot be found.
    """


class EndpointAlreadyExistsError(ApiContextEngineError):
    """
    Raised when an endpoint already exists.
    """


class EndpointNotFoundError(ApiContextEngineError):
    """
    Raised when an endpoint cannot be found.
    """
