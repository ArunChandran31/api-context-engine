from app.parser.extractor import extract_specification


def test_extracts_rich_endpoint_metadata():
    specification = {
        "openapi": "3.0.3",
        "info": {
            "title": "Rich Test API",
            "version": "1.0.0",
        },
        "paths": {
            "/products/{product_id}": {
                "get": {
                    "summary": "Get product",
                    "description": "Returns a product by ID.",
                    "operationId": "getProduct",
                    "parameters": [
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
                    "responses": {
                        "200": {
                            "description": "Product returned successfully",
                        },
                        "404": {
                            "description": "Product not found",
                        },
                    },
                    "security": [
                        {
                            "bearerAuth": [],
                        }
                    ],
                },
                "post": {
                    "summary": "Replace product",
                    "operationId": "replaceProduct",
                    "requestBody": {
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
                    "responses": {
                        "200": {
                            "description": "Product replaced",
                        }
                    },
                },
            }
        },
    }

    parsed = extract_specification(specification)

    assert len(parsed.endpoints) == 2

    get_endpoint = parsed.endpoints[0]

    assert get_endpoint.path == "/products/{product_id}"
    assert get_endpoint.method == "GET"
    assert get_endpoint.summary == "Get product"
    assert get_endpoint.description == "Returns a product by ID."
    assert get_endpoint.operation_id == "getProduct"

    assert get_endpoint.parameters == [
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
    ]

    assert get_endpoint.responses == {
        "200": {
            "description": "Product returned successfully",
        },
        "404": {
            "description": "Product not found",
        },
    }

    assert get_endpoint.security == [
        {
            "bearerAuth": [],
        }
    ]

    post_endpoint = parsed.endpoints[1]

    assert post_endpoint.request_body == {
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
    }

    assert post_endpoint.responses == {
        "200": {
            "description": "Product replaced",
        }
    }
