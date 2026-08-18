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


def test_generate_includes_rich_endpoint_metadata() -> None:
    specification = ApiSpecification(
        id=1,
        title="Rich Test API",
        version="1.0.0",
        description="API with rich endpoint metadata.",
        source_file="rich-api.yaml",
    )

    specification.endpoints = [
        Endpoint(
            id=10,
            api_specification_id=1,
            path="/products/{product_id}",
            method="get",
            summary="Get product",
            description="Returns a product by ID.",
            operation_id="getProduct",
            parameters=[
                {
                    "name": "product_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "ID of the product",
                },
                {
                    "name": "include_reviews",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "boolean"},
                    "description": "Include product reviews",
                },
            ],
            responses={
                "200": {
                    "description": "Product returned successfully",
                },
                "404": {
                    "description": "Product not found",
                },
            },
            security=[
                {
                    "bearerAuth": [],
                }
            ],
        )
    ]

    generator = ContextGenerator()

    documents = generator.generate(specification)

    assert len(documents) == 1

    content = documents[0].content

    assert "Parameters:" in content
    assert '"name": "product_id"' in content
    assert '"in": "path"' in content
    assert '"required": true' in content
    assert '"type": "integer"' in content
    assert '"name": "include_reviews"' in content
    assert '"in": "query"' in content
    assert '"type": "boolean"' in content

    assert "Responses:" in content
    assert '"200"' in content
    assert '"404"' in content
    assert "Product returned successfully" in content
    assert "Product not found" in content

    assert "Security:" in content
    assert '"bearerAuth": []' in content


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


def test_generate_includes_request_body() -> None:
    specification = ApiSpecification(
        id=1,
        title="Rich Test API",
        version="1.0.0",
        description=None,
        source_file="rich-api.yaml",
    )

    specification.endpoints = [
        Endpoint(
            id=20,
            api_specification_id=1,
            path="/products/{product_id}",
            method="post",
            summary="Replace product",
            description=None,
            operation_id="replaceProduct",
            request_body={
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"},
                            },
                        }
                    }
                },
            },
            responses={
                "200": {
                    "description": "Product replaced",
                }
            },
        )
    ]

    generator = ContextGenerator()

    documents = generator.generate(specification)

    assert len(documents) == 1

    content = documents[0].content

    assert "Request Body:" in content
    assert '"required": true' in content
    assert "application/json" in content
    assert '"name": {' in content
    assert '"type": "string"' in content
    assert '"price": {' in content
    assert '"type": "number"' in content

    assert "Responses:" in content
    assert "Product replaced" in content
