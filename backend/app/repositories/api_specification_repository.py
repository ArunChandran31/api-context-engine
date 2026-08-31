from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.models.api_specification import ApiSpecification
from app.repositories.base_repository import BaseRepository


class ApiSpecificationRepository(BaseRepository[ApiSpecification]):
    """
    Repository for API specification specific database operations.

    All user-facing queries are scoped by user_id so one authenticated
    user cannot access another user's API specifications.
    """

    def __init__(self):
        super().__init__(ApiSpecification)

    def get_by_title(
        self,
        db: Session,
        title: str,
        user_id: str | None = None,
    ) -> ApiSpecification | None:
        statement = select(ApiSpecification).where(
            ApiSpecification.title == title,
        )

        if user_id is not None:
            statement = statement.where(
                ApiSpecification.user_id == user_id,
            )

        return db.scalar(statement)

    def exists_by_title(
        self,
        db: Session,
        title: str,
        user_id: str | None = None,
    ) -> bool:
        return (
            self.get_by_title(
                db,
                title,
                user_id,
            )
            is not None
        )

    def get_latest(
        self,
        db: Session,
        user_id: str | None = None,
    ) -> ApiSpecification | None:
        statement = (
            select(ApiSpecification)
            .order_by(desc(ApiSpecification.created_at))
            .limit(1)
        )

        if user_id is not None:
            statement = statement.where(
                ApiSpecification.user_id == user_id,
            )

        return db.scalar(statement)

    def get_by_id_for_user(
        self,
        db: Session,
        specification_id: int,
        user_id: str,
    ) -> ApiSpecification | None:
        statement = select(ApiSpecification).where(
            ApiSpecification.id == specification_id,
            ApiSpecification.user_id == user_id,
        )

        return db.scalar(statement)

    def get_all_for_user(
        self,
        db: Session,
        user_id: str,
    ) -> list[ApiSpecification]:
        statement = (
            select(ApiSpecification)
            .where(
                ApiSpecification.user_id == user_id,
            )
            .order_by(
                desc(ApiSpecification.created_at),
            )
        )

        return list(db.scalars(statement).all())

    def search(
        self,
        db: Session,
        keyword: str,
        user_id: str | None = None,
    ) -> list[ApiSpecification]:
        statement = select(ApiSpecification).where(
            ApiSpecification.title.ilike(
                f"%{keyword}%",
            ),
        )

        if user_id is not None:
            statement = statement.where(
                ApiSpecification.user_id == user_id,
            )

        return list(db.scalars(statement).all())
