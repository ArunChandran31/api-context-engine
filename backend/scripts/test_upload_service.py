from pathlib import Path

from app.database.session import SessionLocal
from app.services.upload_service import UploadService


def main() -> None:
    """
    Manually test the UploadService using a sample
    OpenAPI specification.
    """

    file_path = Path("tests/fixtures/sample_openapi.yaml")

    if not file_path.exists():
        raise FileNotFoundError(f"Test OpenAPI file not found: {file_path}")

    content = file_path.read_bytes()

    db = SessionLocal()

    try:
        service = UploadService()

        result = service.upload(
            db=db,
            content=content,
            filename=file_path.name,
        )

        print("=" * 60)
        print("UPLOAD SUCCESSFUL")
        print("=" * 60)

        print(f"Specification ID : {result.specification_id}")
        print(f"Title            : {result.title}")
        print(f"Version          : {result.version}")
        print(f"Endpoints Created: {result.endpoints_created}")
        print(f"Source File      : {result.filename}")

        print("=" * 60)

    except Exception as exc:
        print("=" * 60)
        print("UPLOAD FAILED")
        print("=" * 60)
        print(f"{type(exc).__name__}: {exc}")
        print("=" * 60)

        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
