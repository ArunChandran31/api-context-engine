import pytest

from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationResult,
)
from app.ai.test_case_validator import TestCaseGroundingValidator


def create_result(
    description: str,
    category: str = "happy",
) -> TestCaseGenerationResult:
    return TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category=category,
                description=description,
            )
        ]
    )


# ---------------------------------------------------------------------------
# STATUS CODE VALIDATION
# ---------------------------------------------------------------------------


def test_validator_accepts_documented_status_code() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "Expect response.status_code == 200.",
    )

    validated = validator.validate(
        result=result,
        context='"200": {"description": "Success"}',
    )

    assert validated == result


def test_validator_rejects_undocumented_status_code() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "Expect response.status_code == 201.",
    )

    with pytest.raises(
        ValueError,
        match="undocumented HTTP status code 201",
    ):
        validator.validate(
            result=result,
            context='"200": {"description": "Success"}',
        )


def test_validator_accepts_documented_http_status() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "The endpoint returns HTTP 404 when the product is not found.",
    )

    validated = validator.validate(
        result=result,
        context='"404": {"description": "Product not found"}',
    )

    assert validated == result


def test_validator_rejects_undocumented_http_status() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "The endpoint returns HTTP 500.",
    )

    with pytest.raises(
        ValueError,
        match="undocumented HTTP status code 500",
    ):
        validator.validate(
            result=result,
            context='"200": {"description": "Success"}',
        )


def test_validator_rejects_undocumented_natural_language_status_code() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        ("The authentication request should receive 401 " "when the token is invalid."),
        category="auth",
    )

    with pytest.raises(
        ValueError,
        match="undocumented HTTP status code 401",
    ):
        validator.validate(
            result=result,
            context=(
                "Endpoint: POST /products/{product_id}\n" "HTTP 200 is documented."
            ),
        )


def test_validator_rejects_undocumented_returns_status_code() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "The request returns 201 on successful authentication.",
        category="auth",
    )

    with pytest.raises(
        ValueError,
        match="undocumented HTTP status code 201",
    ):
        validator.validate(
            result=result,
            context=(
                "Endpoint: POST /products/{product_id}\n" "HTTP 200 is documented."
            ),
        )


def test_validator_rejects_undocumented_responds_with_status_code() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "The API responds with 403 when authentication fails.",
        category="auth",
    )

    with pytest.raises(
        ValueError,
        match="undocumented HTTP status code 403",
    ):
        validator.validate(
            result=result,
            context=(
                "Endpoint: POST /products/{product_id}\n" "HTTP 200 is documented."
            ),
        )


def test_validator_accepts_documented_natural_language_status_code() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "The authenticated request should receive 200.",
        category="auth",
    )

    validated = validator.validate(
        result=result,
        context=("Endpoint: POST /products/{product_id}\n" "HTTP 200 is documented."),
    )

    assert validated == result


def test_validator_accepts_multiple_documented_status_codes() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        Expect 200 for success.
        Expect 400 for invalid product data.
        Expect 404 for missing product.
        """,
    )

    validated = validator.validate(
        result=result,
        context="""
        "200": {"description": "Success"}
        "400": {"description": "Invalid product data"}
        "404": {"description": "Product not found"}
        """,
    )

    assert validated == result


# ---------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------


def test_validator_accepts_documented_permission() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        'Check permission: "products:read".',
    )

    validated = validator.validate(
        result=result,
        context='"products:read"',
    )

    assert validated == result


def test_validator_rejects_undocumented_permission() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        'Check permission: "products:admin".',
    )

    with pytest.raises(
        ValueError,
        match="undocumented authentication permission",
    ):
        validator.validate(
            result=result,
            context='"products:read"',
        )


# ---------------------------------------------------------------------------
# GENERAL VALIDATION
# ---------------------------------------------------------------------------


def test_validator_rejects_empty_context() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        "A generated test.",
    )

    with pytest.raises(
        ValueError,
        match="API context is empty",
    ):
        validator.validate(
            result=result,
            context="",
        )


# ---------------------------------------------------------------------------
# REQUEST VALUES
# ---------------------------------------------------------------------------


def test_validator_accepts_placeholder_request_values() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        {
            "name": "<NAME>",
            "price": "<PRICE>",
            "in_stock": "<IN_STOCK>"
        }
        """,
    )

    validated = validator.validate(
        result=result,
        context="""
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"},
            "in_stock": {"type": "boolean"}
        }
        """,
    )

    assert validated == result


def test_validator_rejects_undocumented_string_request_value() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        {
            "name": "Sample Product"
        }
        """,
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete value",
    ):
        validator.validate(
            result=result,
            context="""
            "properties": {
                "name": {"type": "string"}
            }
            """,
        )


def test_validator_rejects_undocumented_numeric_request_value() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        {
            "price": 19.99
        }
        """,
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete value",
    ):
        validator.validate(
            result=result,
            context="""
            "properties": {
                "price": {"type": "number"}
            }
            """,
        )


def test_validator_accepts_documented_concrete_request_value() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        {
            "category": "electronics"
        }
        """,
    )

    validated = validator.validate(
        result=result,
        context="""
        "category": {
            "enum": [
                "electronics",
                "clothing",
                "books"
            ]
        }
        """,
    )

    assert validated == result


# ---------------------------------------------------------------------------
# JAVASCRIPT / TYPESCRIPT REQUEST-BODY GROUNDING
# ---------------------------------------------------------------------------


def test_validator_rejects_undocumented_javascript_string_value() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: 'Sample Product',
                price: <PRICE>
            });
        """,
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete value",
    ):
        validator.validate(
            result=result,
            context="""
            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number"}
            }
            """,
        )


def test_validator_rejects_undocumented_javascript_numeric_value() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: 9.99
            });
        """,
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete value",
    ):
        validator.validate(
            result=result,
            context="""
            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number"}
            }
            """,
        )


def test_validator_allows_synthetic_invalid_type_in_validation_test() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: 12345,
                price: <PRICE>
            });
        """,
        category="Negative / Validation",
    )

    validated = validator.validate(
        result=result,
        context="""
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"}
        }
        """,
    )

    assert validated == result


def test_validator_allows_synthetic_invalid_string_for_number_field() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: 'free'
            });
        """,
        category="Negative / Validation",
    )

    validated = validator.validate(
        result=result,
        context="""
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"}
        }
        """,
    )

    assert validated == result


def test_validator_rejects_valid_but_undocumented_javascript_value_in_validation() -> (
    None
):
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: 9.99
            });
        """,
        category="Negative / Validation",
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete value",
    ):
        validator.validate(
            result=result,
            context="""
            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number"}
            }
            """,
        )


def test_validator_rejects_undocumented_enum_value() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        {
            "category": "food"
        }
        """,
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete value",
    ):
        validator.validate(
            result=result,
            context="""
            "category": {
                "enum": [
                    "electronics",
                    "clothing",
                    "books"
                ]
            }
            """,
        )


# ---------------------------------------------------------------------------
# PATH PARAMETER GROUNDING
# ---------------------------------------------------------------------------


def test_validator_accepts_placeholder_path_parameter_for_auth() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        describe('POST /products/{product_id}', () => {
            it('uses bearer authentication', async () => {
                const response = await request(app)
                    .post('/products/<PRODUCT_ID>')
                    .set('Authorization', 'Bearer test-token')
                    .send({
                        name: '<NAME>',
                        price: '<PRICE>'
                    });
            });
        });
        """,
        category="auth",
    )

    validated = validator.validate(
        result=result,
        context="""
        Endpoint: POST /products/{product_id}
        HTTP 200 is documented.

        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"}
        }
        """,
    )

    assert validated == result


def test_validator_rejects_undocumented_concrete_path_parameter_for_auth() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        describe('POST /products/{product_id}', () => {
            it('uses bearer authentication', async () => {
                const response = await request(app)
                    .post('/products/123')
                    .set('Authorization', 'Bearer test-token')
                    .send({
                        name: '<NAME>',
                        price: '<PRICE>'
                    });
            });
        });
        """,
        category="auth",
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete path parameter value",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}
            HTTP 200 is documented.

            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number"}
            }
            """,
        )


def test_validator_rejects_undocumented_concrete_path_parameter_for_happy() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/123')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });
        """,
        category="happy",
    )

    with pytest.raises(
        ValueError,
        match="undocumented concrete path parameter value",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}
            HTTP 200 is documented.

            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number"}
            }
            """,
        )


def test_validator_allows_synthetic_path_parameter_for_documented_error() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/999999')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });
        """,
        category="errors",
    )

    validated = validator.validate(
        result=result,
        context="""
        Endpoint: POST /products/{product_id}
        HTTP 404 is documented.

        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"}
        }
        """,
    )

    assert validated == result


def test_validator_accepts_documented_concrete_path_parameter() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/123')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });
        """,
        category="happy",
    )

    validated = validator.validate(
        result=result,
        context="""
        Endpoint: POST /products/{product_id}
        Example request: POST /products/123
        HTTP 200 is documented.

        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"}
        }
        """,
    )

    assert validated == result


def test_validator_rejects_undocumented_numeric_path_parameter() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/0')
            .send({
                price: '<PRICE>',
                in_stock: '<IN_STOCK>'
            });
        """,
        category="Documented HTTP Errors",
    )

    with pytest.raises(
        ValueError,
        match="undocumented.*path",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}
            Path parameters:
                product_id:
                    type: integer
            Request body:
                properties:
                    name:
                        type: string
                    price:
                        type: number
                    in_stock:
                        type: boolean
            Responses:
                400: Invalid product data
            """,
        )


def test_validator_rejects_undocumented_concrete_product_value() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        request
            .post('/products/1')
            .send({
                name: 'Test Product',
                price: 9.99,
                in_stock: true
            });
        """,
        category="Documented HTTP Errors",
    )

    with pytest.raises(
        ValueError,
        match="undocumented",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}
            Path parameters:
                product_id:
                    type: integer
            Request body:
                properties:
                    name:
                        type: string
                    price:
                        type: number
                    in_stock:
                        type: boolean
            Responses:
                400: Invalid product data
            """,
        )


# ---------------------------------------------------------------------------
# RESPONSE-BODY GROUNDING
# ---------------------------------------------------------------------------


def test_validator_rejects_response_property_without_response_schema() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        expect(response.status).toBe(200);
        expect(response.body.id).toBeDefined();
        """,
        category="happy",
    )

    with pytest.raises(
        ValueError,
        match="response.*schema|response.*property|undocumented",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}

            Request Body:
            {
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "price": {
                        "type": "number"
                    }
                }
            }

            Responses:
            {
                "200": {
                    "description": "Product replaced successfully"
                }
            }
            """,
        )


def test_validator_rejects_response_property_inferred_from_request_body() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        expect(response.status).toBe(200);
        expect(response.body.name).toBe('<NAME>');
        """,
        category="happy",
    )

    with pytest.raises(
        ValueError,
        match="response.*property|undocumented|response.*schema",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}

            Request Body:
            {
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "price": {
                        "type": "number"
                    }
                }
            }

            Responses:
            {
                "200": {
                    "description": "Product replaced successfully"
                }
            }
            """,
        )


def test_validator_rejects_undocumented_response_property() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        expect(response.status).toBe(200);
        expect(response.body.name).toBeDefined();
        """,
        category="happy",
    )

    with pytest.raises(
        ValueError,
        match="undocumented.*response|response.*property",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}

            Request Body:
            {
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "price": {
                        "type": "number"
                    }
                }
            }

            Responses:
            {
                "200": {
                    "description": "Product replaced successfully",
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {
                                    "id": {
                                        "type": "integer"
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """,
        )


def test_validator_accepts_documented_response_property() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        expect(response.status).toBe(200);
        expect(response.body.id).toBeDefined();
        """,
        category="happy",
    )

    validated = validator.validate(
        result=result,
        context="""
        Endpoint: POST /products/{product_id}

        Request Body:
        {
            "properties": {
                "name": {
                    "type": "string"
                },
                "price": {
                    "type": "number"
                }
            }
        }

        Responses:
        {
            "200": {
                "description": "Product replaced successfully",
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "id": {
                                    "type": "integer"
                                }
                            }
                        }
                    }
                }
            }
        }
        """,
    )

    assert validated == result


def test_validator_rejects_response_property_when_only_request_field_is_documented() -> (
    None
):
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        expect(response.status).toBe(200);
        expect(response.body.price).toBe('<PRICE>');
        """,
        category="happy",
    )

    with pytest.raises(
        ValueError,
        match="response.*property|undocumented|response.*schema",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}

            Request Body:
            {
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "price": {
                        "type": "number"
                    }
                }
            }

            Responses:
            {
                "200": {
                    "description": "Product replaced successfully"
                }
            }
            """,
        )


# ---------------------------------------------------------------------------
# INFERRED RESPONSE / SUCCESS BEHAVIOR
# ---------------------------------------------------------------------------


def test_validator_rejects_undocumented_success_status_for_optional_field_omission() -> (
    None
):
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        // in_stock is omitted because it is optional.
        expect(response.status).toBe(200);
        """,
        category="edge",
    )

    with pytest.raises(
        ValueError,
        match="undocumented HTTP status code|undocumented.*success|inferred",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}

            Request Body:
            {
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

            Responses:
            {
                "200": {
                    "description": "Product replaced successfully"
                },
                "400": {
                    "description": "Invalid product data"
                }
            }
            """,
        )


def test_validator_rejects_inferred_response_field_from_request_field() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        expect(response.status).toBe(200);
        expect(response.body.name).toBe('<NAME>');
        expect(response.body.price).toBe('<PRICE>');
        """,
        category="happy",
    )

    with pytest.raises(
        ValueError,
        match="response.*property|undocumented|response.*schema",
    ):
        validator.validate(
            result=result,
            context="""
            Endpoint: POST /products/{product_id}

            Request Body:
            {
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "price": {
                        "type": "number"
                    }
                }
            }

            Responses:
            {
                "200": {
                    "description": "Product replaced successfully"
                }
            }
            """,
        )


def test_validator_accepts_documented_response_schema_and_status_together() -> None:
    validator = TestCaseGroundingValidator()

    result = create_result(
        """
        const response = await request
            .post('/products/<PRODUCT_ID>')
            .send({
                name: '<NAME>',
                price: '<PRICE>'
            });

        expect(response.status).toBe(200);
        expect(response.body.id).toBeDefined();
        """,
        category="happy",
    )

    validated = validator.validate(
        result=result,
        context="""
        Endpoint: POST /products/{product_id}

        Request Body:
        {
            "properties": {
                "name": {
                    "type": "string"
                },
                "price": {
                    "type": "number"
                }
            }
        }

        Responses:
        {
            "200": {
                "description": "Product replaced successfully",
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "id": {
                                    "type": "integer"
                                }
                            }
                        }
                    }
                }
            }
        }
        """,
    )

    assert validated == result
