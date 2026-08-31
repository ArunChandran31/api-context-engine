from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models.endpoint import Endpoint
from app.repositories.base_repository import BaseRepository


class EndpointRepository(BaseRepository[Endpoint]):
    """
    Repository for Endpoint database operations.
    """

    def __init__(self):
        super().__init__(Endpoint)

    def get_by_specification(
        self,
        db: Session,
        specification_id: int,
    ) -> list[Endpoint]:
        statement = select(Endpoint).where(
            Endpoint.api_specification_id == specification_id,
        )

        return list(db.scalars(statement).all())

    def get_by_method(
        self,
        db: Session,
        method: str,
    ) -> list[Endpoint]:
        statement = select(Endpoint).where(
            Endpoint.method == method.upper(),
        )

        return list(db.scalars(statement).all())

    def get_by_path(
        self,
        db: Session,
        path: str,
    ) -> list[Endpoint]:
        statement = select(Endpoint).where(
            Endpoint.path == path,
        )

        return list(db.scalars(statement).all())

    def get_by_path_and_method(
        self,
        db: Session,
        specification_id: int,
        path: str,
        method: str,
    ) -> Endpoint | None:
        statement = select(Endpoint).where(
            Endpoint.api_specification_id == specification_id,
            Endpoint.path == path,
            Endpoint.method == method.upper(),
        )

        return db.scalar(statement)

    def exists(
        self,
        db: Session,
        specification_id: int,
        path: str,
        method: str,
    ) -> bool:
        return (
            self.get_by_path_and_method(
                db,
                specification_id,
                path,
                method,
            )
            is not None
        )

    def count(
        self,
        db: Session,
        specification_id: int,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Endpoint)
            .where(
                Endpoint.api_specification_id == specification_id,
            )
        )

        return db.scalar(statement) or 0

    def delete_by_specification(
        self,
        db: Session,
        specification_id: int,
    ) -> int:
        """
        Delete all endpoints belonging to a specification.

        The deletion is intentionally not committed here.
        Transaction ownership remains with the caller.
        """

        endpoints = self.get_by_specification(
            db,
            specification_id,
        )

        for endpoint in endpoints:
            self.delete(
                db,
                endpoint,
            )

        return len(endpoints)
