from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.rag.context_generator import ContextGenerator


def test_generate_endpoint_documents() -> None:
    specification = ApiSpecification(
        id=1,
        title="User API",
        version="1.0.0",
        description="API for managing users.",
        source_file="users.yaml",
    )

    specification.endpoints = [
        Endpoint(
            id=10,
            api_specification_id=1,
            path="/users",
            method="post",
            summary="Create user",
            description="Creates a new user account.",
            operation_id="createUser",
        ),
        Endpoint(
            id=11,
            api_specification_id=1,
            path="/users/{user_id}",
            method="get",
            summary="Get user",
            description="Returns a user by ID.",
            operation_id="getUser",
        ),
    ]

    generator = ContextGenerator()

    documents = generator.generate(specification)

    assert len(documents) == 2

    first = documents[0]

    assert first.specification_id == 1
    assert first.endpoint_id == 10
    assert first.path == "/users"
    assert first.method == "POST"
    assert first.operation_id == "createUser"

    assert "API: User API" in first.content
    assert "Version: 1.0.0" in first.content
    assert "Endpoint: POST /users" in first.content
    assert "Summary: Create user" in first.content
    assert "Description: Creates a new user account." in first.content
    assert "Operation ID: createUser" in first.content

    assert first.metadata["api_title"] == "User API"
    assert first.metadata["api_version"] == "1.0.0"
    assert first.metadata["source_file"] == "users.yaml"


def test_generate_handles_optional_endpoint_fields() -> None:
    specification = ApiSpecification(
        id=1,
        title="Minimal API",
        version=None,
        description=None,
        source_file="minimal.yaml",
    )

    specification.endpoints = [
        Endpoint(
            id=20,
            api_specification_id=1,
            path="/health",
            method="get",
            summary=None,
            description=None,
            operation_id=None,
        )
    ]

    generator = ContextGenerator()

    documents = generator.generate(specification)

    assert len(documents) == 1

    document = documents[0]

    assert document.content == "API: Minimal API\nEndpoint: GET /health"

    assert document.operation_id is None


def test_generate_returns_empty_list_for_specification_without_endpoints() -> None:
    specification = ApiSpecification(
        id=1,
        title="Empty API",
        version="1.0.0",
        description=None,
        source_file="empty.yaml",
    )

    specification.endpoints = []

    generator = ContextGenerator()

    documents = generator.generate(specification)

    assert documents == []
