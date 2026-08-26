from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.models.api_specification import ApiSpecification
from app.repositories.base_repository import BaseRepository


class ApiSpecificationRepository(BaseRepository[ApiSpecification]):
    """
    Repository for API specification specific database operations.
    """

    def __init__(self):
        super().__init__(ApiSpecification)

    def get_by_title(
        self,
        db: Session,
        title: str,
    ) -> ApiSpecification | None:
        statement = select(ApiSpecification).where(
            ApiSpecification.title == title,
        )

        return db.scalar(statement)

    def exists_by_title(
        self,
        db: Session,
        title: str,
    ) -> bool:
        return (
            self.get_by_title(
                db,
                title,
            )
            is not None
        )

    def get_latest(
        self,
        db: Session,
    ) -> ApiSpecification | None:
        statement = (
            select(ApiSpecification)
            .order_by(desc(ApiSpecification.created_at))
            .limit(1)
        )

        return db.scalar(statement)

    def search(
        self,
        db: Session,
        keyword: str,
    ) -> list[ApiSpecification]:
        statement = select(ApiSpecification).where(
            ApiSpecification.title.ilike(
                f"%{keyword}%",
            ),
        )

        return list(db.scalars(statement).all())
