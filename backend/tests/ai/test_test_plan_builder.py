from app.ai.test_plan_builder import TestPlanBuilder
from app.rag.retrieval_service import RetrievalResult


def create_context() -> RetrievalResult:
    return RetrievalResult(
        content="""
        API: Rich Products API
        Endpoint: POST /products/{product_id}

        Parameters:
        [
            {
                "name": "product_id",
                "in": "path",
                "required": true,
                "schema": {
                    "type": "integer"
                }
            }
        ]

        Request Body:
        {
            "schema": {
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "price": {
                        "type": "number"
                    },
                    "in_stock": {
                        "type": "boolean"
                    }
                },
                "required": [
                    "name",
                    "price"
                ]
            }
        }

        Responses:
        {
            "200": {
                "description": "Product replaced successfully"
            },
            "400": {
                "description": "Invalid product data"
            },
            "404": {
                "description": "Product not found"
            }
        }

        Security:
        [
            {
                "bearerAuth": []
            }
        ]
        """,
        score=0.95,
        metadata={},
    )


def test_builder_returns_test_plan() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
    )

    assert plan.endpoint == "POST /products/{product_id}"
    assert plan.items


def test_builder_detects_happy_path() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["happy"],
    )

    assert any(item.category == "happy" for item in plan.items)


def test_builder_detects_required_fields() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["validation"],
    )

    descriptions = " ".join(item.description for item in plan.items)

    assert "name" in descriptions
    assert "price" in descriptions


def test_builder_does_not_create_edge_case_without_explicit_constraint() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["edge"],
    )

    edge_items = [item for item in plan.items if item.category == "edge"]

    assert edge_items == []


def test_builder_creates_edge_case_for_explicit_constraint() -> None:
    builder = TestPlanBuilder()

    context = create_context()

    edge_context = RetrievalResult(
        content=context.content.replace(
            '"price": {\n'
            '                        "type": "number"\n'
            "                    }",
            '"price": {\n'
            '                        "type": "number",\n'
            '                        "minimum": 0,\n'
            '                        "maximum": 10000\n'
            "                    }",
        ),
        score=context.score,
        metadata=context.metadata,
    )

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[edge_context],
        categories=["edge"],
    )

    edge_items = [item for item in plan.items if item.category == "edge"]

    assert edge_items

    grounded_facts = " ".join(
        fact for item in edge_items for fact in item.grounded_facts
    )

    assert "minimum=0" in grounded_facts
    assert "maximum=10000" in grounded_facts

    assert len(edge_items) == 2

    descriptions = " ".join(item.description for item in edge_items)

    assert "minimum=0" in descriptions
    assert "maximum=10000" in descriptions


def test_builder_detects_authentication() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["auth"],
    )

    assert any(item.category == "auth" for item in plan.items)


def test_builder_detects_documented_errors() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["errors"],
    )

    descriptions = " ".join(item.description for item in plan.items)

    assert "400" in descriptions
    assert "404" in descriptions


def test_builder_returns_limitation_without_context() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[],
    )

    assert plan.items
    assert "unavailable" in plan.items[0].description.lower()


def test_builder_includes_required_fields_in_error_grounding_facts() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["errors"],
    )

    error_items = [item for item in plan.items if item.category == "errors"]

    assert error_items

    grounded_facts = " ".join(
        fact for item in error_items for fact in item.grounded_facts
    )

    assert "Request field 'name' is documented as required." in grounded_facts

    assert "Request field 'price' is documented as required." in grounded_facts


def test_builder_includes_path_parameter_in_error_grounding_facts() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["errors"],
    )

    error_items = [item for item in plan.items if item.category == "errors"]

    assert error_items

    grounded_facts = " ".join(
        fact for item in error_items for fact in item.grounded_facts
    )

    assert (
        "Path parameter 'product_id' is documented as type 'integer'." in grounded_facts
    )


def test_builder_preserves_documented_error_descriptions() -> None:
    builder = TestPlanBuilder()

    plan = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["errors"],
    )

    descriptions = " ".join(
        item.description for item in plan.items if item.category == "errors"
    )

    assert "Invalid product data" in descriptions
    assert "Product not found" in descriptions
