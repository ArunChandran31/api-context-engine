from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.database.session import SessionLocal


def main():
    db = SessionLocal()

    api = ApiSpecification(
        title="Pet Store API",
        version="1.0.0",
        description="Sample API",
        source_file="petstore.yaml",
    )

    api.endpoints = [
        Endpoint(
            path="/pets",
            method="GET",
            summary="List Pets",
        ),
        Endpoint(
            path="/pets",
            method="POST",
            summary="Create Pet",
        ),
    ]

    db.add(api)

    db.commit()

    db.close()

    print("Sample data inserted successfully.")


if __name__ == "__main__":
    main()
