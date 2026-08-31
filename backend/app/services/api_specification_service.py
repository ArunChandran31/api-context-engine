from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser
from app.database.models.api_specification import ApiSpecification
from app.exceptions import SpecificationAlreadyExistsError
from app.repositories.api_specification_repository import (
    ApiSpecificationRepository,
)
from app.schemas.api_specification import ApiSpecificationCreate


class ApiSpecificationService:
    """
    Business logic for API specifications.

    User-facing operations are scoped to the authenticated
    Supabase user.
    """

    def __init__(self):
        self.repository = ApiSpecificationRepository()

    def create_entity(
        self,
        db: Session,
        specification: ApiSpecificationCreate,
        user: AuthenticatedUser | None = None,
    ) -> ApiSpecification:
        """
        Create an API specification inside the current transaction.

        This method does NOT commit or rollback.
        Transaction ownership belongs to the caller.
        """

        user_id = user.id if user is not None else None

        if self.repository.exists_by_title(
            db,
            specification.title,
            user_id,
        ):
            raise SpecificationAlreadyExistsError(
                f"API specification '{specification.title}' already exists."
            )

        entity = ApiSpecification(
            title=specification.title,
            version=specification.version,
            description=specification.description,
            base_url=specification.base_url,
            source_file=specification.source_file,
            user_id=user_id,
        )

        return self.repository.add(
            db,
            entity,
        )

    def create(
        self,
        db: Session,
        specification: ApiSpecificationCreate,
        user: AuthenticatedUser | None = None,
    ) -> ApiSpecification:
        """
        Create a standalone API specification.

        This method owns the transaction.
        """

        try:
            entity = self.create_entity(
                db,
                specification,
                user,
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
        user: AuthenticatedUser | None = None,
    ) -> ApiSpecification | None:
        """
        Get a specification.

        When a user is supplied, ownership is enforced.
        """

        if user is None:
            return self.repository.get_by_id(
                db,
                specification_id,
            )

        return self.repository.get_by_id_for_user(
            db,
            specification_id,
            user.id,
        )

    def list(
        self,
        db: Session,
        user: AuthenticatedUser | None = None,
    ) -> list[ApiSpecification]:
        """
        List specifications.

        Authenticated requests only receive specifications owned
        by the authenticated user.
        """

        if user is None:
            return self.repository.get_all(db)

        return self.repository.get_all_for_user(
            db,
            user.id,
        )

    def update_from_parsed(
        self,
        specification: ApiSpecification,
        *,
        title: str,
        version: str | None,
        description: str | None,
        base_url: str | None,
        source_file: str,
    ) -> ApiSpecification:
        """
        Update specification metadata inside the current transaction.

        This method does NOT commit or rollback.
        """

        specification.title = title
        specification.version = version
        specification.description = description
        specification.base_url = base_url
        specification.source_file = source_file

        return specification

    def belongs_to_user(
        self,
        db: Session,
        specification_id: int,
        user: AuthenticatedUser,
    ) -> bool:
        return (
            self.repository.get_by_id_for_user(
                db,
                specification_id,
                user.id,
            )
            is not None
        )
