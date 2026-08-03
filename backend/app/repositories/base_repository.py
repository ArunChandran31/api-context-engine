from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for SQLAlchemy models.

    This repository performs CRUD operations without committing
    the transaction. The caller (typically a service) is responsible
    for commit() or rollback().
    """

    def __init__(self, model: type[ModelType]):
        self.model = model

    def add(self, db: Session, entity: ModelType) -> ModelType:
        db.add(entity)
        db.flush()
        db.refresh(entity)
        return entity

    def get_by_id(self, db: Session, entity_id: int) -> ModelType | None:
        return db.get(self.model, entity_id)

    def get_all(self, db: Session) -> list[ModelType]:
        statement = select(self.model)
        return list(db.scalars(statement).all())

    def delete(self, db: Session, entity: ModelType) -> None:
        db.delete(entity)

    def exists(self, db: Session, entity_id: int) -> bool:
        return db.get(self.model, entity_id) is not None
