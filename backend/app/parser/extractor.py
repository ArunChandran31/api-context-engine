from app.parser.models import ApiMetadata, Endpoint


def extract_metadata(spec: dict) -> ApiMetadata:
    info = spec.get("info", {})
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            endpoints.append(
                Endpoint(
                    path=path,
                    method=method.upper(),
                    summary=details.get("summary"),
                )
            )

    return ApiMetadata(
        title=info.get("title", "Unknown API"),
        version=info.get("version", "Unknown"),
        endpoints=endpoints,
    )