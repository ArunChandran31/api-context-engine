from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import AuthenticatedUser, get_current_user
from app.database.base import Base
from app.database.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite://"

TEST_USER = AuthenticatedUser(
    id="test-user-id",
    email="test@example.com",
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Create an isolated in-memory SQLite database for each test.

    API tests must never depend on the real development database.
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


@pytest.fixture(autouse=True)
def override_dependencies(
    db_session: Session,
) -> Generator[None, None, None]:
    """
    Override authentication and database dependencies for API tests.

    Every API test runs as TEST_USER against an isolated in-memory
    SQLite database.
    """

    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        yield
    finally:
        app.dependency_overrides.clear()
