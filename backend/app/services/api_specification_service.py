from sqlalchemy.orm import Session

from app.database.models.api_specification import ApiSpecification
from app.exceptions import SpecificationAlreadyExistsError
from app.repositories.api_specification_repository import (
    ApiSpecificationRepository,
)
from app.schemas.api_specification import ApiSpecificationCreate


class ApiSpecificationService:
    """
    Business logic for API specifications.
    """

    def __init__(self):
        self.repository = ApiSpecificationRepository()

    def create_entity(
        self,
        db: Session,
        specification: ApiSpecificationCreate,
    ) -> ApiSpecification:
        """
        Create an API specification inside the current transaction.

        This method does NOT commit or rollback.
        Transaction ownership belongs to the caller.
        """

        if self.repository.exists_by_title(
            db,
            specification.title,
        ):
            raise SpecificationAlreadyExistsError(
                f"API specification '{specification.title}' already exists."
            )

        entity = ApiSpecification(
            title=specification.title,
            version=specification.version,
            description=specification.description,
            source_file=specification.source_file,
        )

        return self.repository.add(db, entity)

    def create(
        self,
        db: Session,
        specification: ApiSpecificationCreate,
    ) -> ApiSpecification:
        """
        Create a standalone API specification.

        This method owns the transaction.
        """

        try:
            entity = self.create_entity(
                db,
                specification,
            )

            db.commit()
            db.refresh(entity)

            return entity

        except Exception:
            db.rollback()
            raise

    def get(
        self,
        db: Session,
        specification_id: int,
    ) -> ApiSpecification | None:
        return self.repository.get_by_id(
            db,
            specification_id,
        )

    def list(
        self,
        db: Session,
    ) -> list[ApiSpecification]:
        return self.repository.get_all(db)
