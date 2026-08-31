from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.rag.indexing_orchestrator import RAGIndexingOrchestrator
from app.services.upload_service import UploadService

TEST_DATABASE_URL = "sqlite://"


@pytest.fixture
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def initial_openapi_content() -> bytes:
    return b"""
openapi: 3.0.0
info:
  title: Replacement Test API
  version: 1.0.0
  description: Original API
paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      responses:
        '200':
          description: Users returned
  /users/{user_id}:
    get:
      summary: Get user
      operationId: getUser
      parameters:
        - in: path
          name: user_id
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: User returned
"""


@pytest.fixture
def replacement_openapi_content() -> bytes:
    return b"""
openapi: 3.0.0
info:
  title: Replacement Test API V2
  version: 2.0.0
  description: Updated API
servers:
  - url: https://example.com/api
paths:
  /products:
    get:
      summary: List products
      operationId: listProducts
      responses:
        '200':
          description: Products returned
  /products/{product_id}:
    delete:
      summary: Delete product
      operationId: deleteProduct
      parameters:
        - in: path
          name: product_id
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Product deleted
  /health:
    get:
      summary: Health check
      operationId: healthCheck
      responses:
        '200':
          description: Healthy
"""


@pytest.fixture
def rag_indexing_orchestrator() -> MagicMock:
    return MagicMock(
        spec=RAGIndexingOrchestrator,
    )


def get_endpoints(
    db: Session,
    specification_id: int,
) -> list[Endpoint]:
    return list(
        db.scalars(
            select(Endpoint).where(
                Endpoint.api_specification_id == specification_id,
            ),
        ).all(),
    )


def test_replace_updates_specification_and_replaces_endpoints(
    db_session: Session,
    initial_openapi_content: bytes,
    replacement_openapi_content: bytes,
    rag_indexing_orchestrator: MagicMock,
):
    service = UploadService(
        rag_indexing_orchestrator=rag_indexing_orchestrator,
    )

    initial_result = service.upload(
        db=db_session,
        content=initial_openapi_content,
        filename="initial.yaml",
    )

    rag_indexing_orchestrator.index_specification.reset_mock()

    result = service.replace(
        db=db_session,
        specification_id=initial_result.specification_id,
        content=replacement_openapi_content,
        filename="replacement.yaml",
    )

    assert result.specification_id == initial_result.specification_id
    assert result.title == "Replacement Test API V2"
    assert result.version == "2.0.0"
    assert result.endpoints_created == 3
    assert result.filename == "replacement.yaml"

    specification = db_session.get(
        ApiSpecification,
        result.specification_id,
    )

    assert specification is not None
    assert specification.title == "Replacement Test API V2"
    assert specification.version == "2.0.0"
    assert specification.description == "Updated API"
    assert specification.base_url == "https://example.com/api"
    assert specification.source_file == "replacement.yaml"

    endpoints = get_endpoints(
        db_session,
        result.specification_id,
    )

    assert len(endpoints) == 3

    endpoint_keys = {(endpoint.method, endpoint.path) for endpoint in endpoints}

    assert endpoint_keys == {
        ("GET", "/products"),
        ("DELETE", "/products/{product_id}"),
        ("GET", "/health"),
    }

    assert rag_indexing_orchestrator.index_specification.call_count == 1

    indexed_specification = (
        rag_indexing_orchestrator.index_specification.call_args.args[0]
    )

    assert indexed_specification.id == result.specification_id
    assert indexed_specification.title == "Replacement Test API V2"


def test_replace_rolls_back_when_endpoint_creation_fails(
    db_session: Session,
    initial_openapi_content: bytes,
    replacement_openapi_content: bytes,
    monkeypatch: pytest.MonkeyPatch,
    rag_indexing_orchestrator: MagicMock,
):
    service = UploadService(
        rag_indexing_orchestrator=rag_indexing_orchestrator,
    )

    initial_result = service.upload(
        db=db_session,
        content=initial_openapi_content,
        filename="initial.yaml",
    )

    rag_indexing_orchestrator.index_specification.reset_mock()

    def fail_endpoint_creation(*args, **kwargs):
        raise RuntimeError(
            "Simulated replacement endpoint failure",
        )

    monkeypatch.setattr(
        service.endpoint_service,
        "create_many_entities",
        fail_endpoint_creation,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated replacement endpoint failure",
    ):
        service.replace(
            db=db_session,
            specification_id=initial_result.specification_id,
            content=replacement_openapi_content,
            filename="replacement.yaml",
        )

    specification = db_session.get(
        ApiSpecification,
        initial_result.specification_id,
    )

    assert specification is not None
    assert specification.title == "Replacement Test API"
    assert specification.version == "1.0.0"
    assert specification.description == "Original API"
    assert specification.source_file == "initial.yaml"

    endpoints = get_endpoints(
        db_session,
        initial_result.specification_id,
    )

    assert len(endpoints) == 2

    endpoint_keys = {(endpoint.method, endpoint.path) for endpoint in endpoints}

    assert endpoint_keys == {
        ("GET", "/users"),
        ("GET", "/users/{user_id}"),
    }

    rag_indexing_orchestrator.index_specification.assert_not_called()


def test_replace_returns_error_for_missing_specification(
    db_session: Session,
    replacement_openapi_content: bytes,
    rag_indexing_orchestrator: MagicMock,
):
    service = UploadService(
        rag_indexing_orchestrator=rag_indexing_orchestrator,
    )

    with pytest.raises(
        ValueError,
        match="API specification with ID 999 was not found",
    ):
        service.replace(
            db=db_session,
            specification_id=999,
            content=replacement_openapi_content,
            filename="replacement.yaml",
        )

    rag_indexing_orchestrator.index_specification.assert_not_called()
