from app.core.auth import AuthenticatedUser, get_current_user
from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.database.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

USER_A = AuthenticatedUser(
    id="user-a-id",
    email="user-a@example.com",
)

USER_B = AuthenticatedUser(
    id="user-b-id",
    email="user-b@example.com",
)


def set_user(user: AuthenticatedUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


def get_test_db() -> Session:
    """
    Return the isolated database session configured by tests/conftest.py.
    """

    db = app.dependency_overrides.get(get_db)

    if db is None:
        raise RuntimeError("The get_db dependency override is not configured.")

    session = db()

    if not isinstance(session, Session):
        raise RuntimeError("The get_db dependency override did not return a Session.")

    return session


def create_specification(
    user: AuthenticatedUser,
    *,
    title: str,
) -> int:
    """
    Insert a specification directly into the isolated test database.
    """

    db = get_test_db()

    try:
        specification = ApiSpecification(
            title=title,
            version="1.0.0",
            description=f"{title} description",
            base_url="https://example.com",
            source_file=f"{title.lower().replace(' ', '-')}.json",
            user_id=user.id,
        )

        db.add(specification)
        db.commit()
        db.refresh(specification)

        return specification.id

    finally:
        db.close()


def create_endpoint(
    user: AuthenticatedUser,
    specification_id: int,
) -> int:
    """
    Insert an endpoint into a specification owned by the supplied user.
    """

    db = get_test_db()

    try:
        specification = db.get(
            ApiSpecification,
            specification_id,
        )

        assert specification is not None
        assert specification.user_id == user.id

        endpoint = Endpoint(
            api_specification_id=specification_id,
            path="/pets",
            method="GET",
            summary="List pets",
            description="Returns pets.",
            operation_id="listPets",
            parameters=[],
            request_body=None,
            responses={
                "200": {
                    "description": "Successful response",
                },
            },
            security=None,
        )

        db.add(endpoint)
        db.commit()
        db.refresh(endpoint)

        return endpoint.id

    finally:
        db.close()


def test_user_can_access_own_specification() -> None:
    set_user(USER_A)

    specification_id = create_specification(
        USER_A,
        title="User A API",
    )

    client = TestClient(app)

    response = client.get(
        f"/api/specifications/{specification_id}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == specification_id
    assert body["title"] == "User A API"


def test_user_cannot_access_another_users_specification() -> None:
    set_user(USER_A)

    specification_id = create_specification(
        USER_A,
        title="User A Private API",
    )

    set_user(USER_B)

    client = TestClient(app)

    response = client.get(
        f"/api/specifications/{specification_id}",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (f"API specification with ID " f"{specification_id} was not found."),
    }


def test_user_only_sees_own_specifications_in_list() -> None:
    set_user(USER_A)

    user_a_specification_id = create_specification(
        USER_A,
        title="User A API",
    )

    set_user(USER_B)

    user_b_specification_id = create_specification(
        USER_B,
        title="User B API",
    )

    client = TestClient(app)

    response = client.get(
        "/api/specifications",
    )

    assert response.status_code == 200

    specifications = response.json()

    specification_ids = {specification["id"] for specification in specifications}

    assert user_b_specification_id in specification_ids
    assert user_a_specification_id not in specification_ids

    assert all(
        specification["title"] != "User A API" for specification in specifications
    )


def test_user_cannot_access_another_users_endpoints() -> None:
    set_user(USER_A)

    specification_id = create_specification(
        USER_A,
        title="User A Endpoint API",
    )

    endpoint_id = create_endpoint(
        USER_A,
        specification_id,
    )

    assert endpoint_id > 0

    set_user(USER_B)

    client = TestClient(app)

    response = client.get(
        f"/api/endpoints/specification/{specification_id}",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "API specification not found.",
    }


def test_user_can_access_endpoints_for_own_specification() -> None:
    set_user(USER_A)

    specification_id = create_specification(
        USER_A,
        title="User A Endpoint Access API",
    )

    endpoint_id = create_endpoint(
        USER_A,
        specification_id,
    )

    client = TestClient(app)

    response = client.get(
        f"/api/endpoints/specification/{specification_id}",
    )

    assert response.status_code == 200

    endpoints = response.json()

    assert len(endpoints) == 1
    assert endpoints[0]["id"] == endpoint_id
    assert endpoints[0]["path"] == "/pets"
    assert endpoints[0]["method"] == "GET"


def test_user_cannot_use_another_users_specification_for_ai_question() -> None:
    set_user(USER_A)

    specification_id = create_specification(
        USER_A,
        title="User A AI API",
    )

    set_user(USER_B)

    client = TestClient(app)

    response = client.post(
        "/api/ai/question",
        json={
            "question": "What endpoints are available?",
            "specification_id": specification_id,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "API specification not found.",
    }


def test_user_cannot_use_another_users_specification_for_rag_query() -> None:
    set_user(USER_A)

    specification_id = create_specification(
        USER_A,
        title="User A RAG API",
    )

    set_user(USER_B)

    client = TestClient(app)

    response = client.post(
        "/api/rag/query",
        json={
            "query": "What endpoints are available?",
            "specification_id": specification_id,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "API specification not found.",
    }
