from typing import Any

from app.parser.models import ParsedEndpoint, ParsedSpecification

HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "trace",
}


def extract_specification(
    specification: dict[str, Any],
) -> ParsedSpecification:
    """
    Extract API metadata and endpoints from a loaded
    OpenAPI specification.
    """

    info = specification.get("info", {})

    title = info.get("title", "Untitled API")
    version = info.get("version")
    description = info.get("description")
    servers = specification.get("servers", [])
    base_url = None

    if servers and isinstance(servers[0], dict):
        base_url = servers[0].get("url")

    endpoints: list[ParsedEndpoint] = []

    paths = specification.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            method_lower = method.lower()

            # Ignore OpenAPI path-level fields such as "parameters".
            if method_lower not in HTTP_METHODS:
                continue

            if not isinstance(operation, dict):
                operation = {}

            endpoints.append(
                ParsedEndpoint(
                    path=path,
                    method=method_lower.upper(),
                    summary=operation.get("summary"),
                    description=operation.get("description"),
                    operation_id=operation.get("operationId"),
                    parameters=operation.get("parameters"),
                    request_body=operation.get("requestBody"),
                    responses=operation.get("responses"),
                    security=operation.get("security"),
                )
            )

    return ParsedSpecification(
        title=title,
        version=version,
        description=description,
        base_url=base_url,
        endpoints=endpoints,
    )
