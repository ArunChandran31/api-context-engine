import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.services.upload_service import UploadService

TEST_DATABASE_URL = "sqlite://"


@pytest.fixture
def db_session():
    """
    Create an isolated in-memory SQLite database
    for each test.
    """

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
def valid_openapi_content() -> bytes:
    """
    Valid OpenAPI specification containing two endpoints.
    """

    return b"""
openapi: 3.0.0

info:
  title: Transaction Test API
  version: 1.0.0
  description: Used for Unit of Work transaction testing

paths:
  /users:
    get:
      summary: List users
      operationId: listUsers

    post:
      summary: Create user
      operationId: createUser
"""


def count_specifications(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(ApiSpecification)) or 0


def count_endpoints(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Endpoint)) or 0


def test_upload_commits_specification_and_endpoints(
    db_session: Session,
    valid_openapi_content: bytes,
):
    """
    A successful upload must persist both the
    specification and all extracted endpoints.
    """

    service = UploadService()

    result = service.upload(
        db=db_session,
        content=valid_openapi_content,
        filename="transaction-test.yaml",
    )

    assert result.title == "Transaction Test API"
    assert result.version == "1.0.0"
    assert result.endpoints_created == 2

    assert count_specifications(db_session) == 1
    assert count_endpoints(db_session) == 2


def test_upload_rolls_back_when_endpoint_creation_fails(
    db_session: Session,
    valid_openapi_content: bytes,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    If endpoint persistence fails after the specification
    has been flushed, the entire transaction must roll back.
    """

    service = UploadService()

    def fail_endpoint_creation(*args, **kwargs):
        raise RuntimeError("Simulated endpoint persistence failure")

    monkeypatch.setattr(
        service.endpoint_service,
        "create_many_entities",
        fail_endpoint_creation,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated endpoint persistence failure",
    ):
        service.upload(
            db=db_session,
            content=valid_openapi_content,
            filename="rollback-test.yaml",
        )

    assert count_specifications(db_session) == 0
    assert count_endpoints(db_session) == 0
