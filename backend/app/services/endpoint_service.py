from sqlalchemy.orm import Session

from app.database.models.endpoint import Endpoint
from app.exceptions import EndpointAlreadyExistsError
from app.repositories.endpoint_repository import EndpointRepository
from app.schemas.endpoint import EndpointCreate


class EndpointService:
    """
    Business logic for API endpoints.
    """

    def __init__(self):
        self.repository = EndpointRepository()

    def create_entity(
        self,
        db: Session,
        endpoint: EndpointCreate,
    ) -> Endpoint:
        """
        Create an endpoint inside the current transaction.

        This method does NOT commit or rollback.
        """

        if self.repository.exists(
            db,
            endpoint.api_specification_id,
            endpoint.path,
            endpoint.method,
        ):
            raise EndpointAlreadyExistsError(
                f"{endpoint.method.upper()} {endpoint.path} already exists."
            )

        entity = Endpoint(
            api_specification_id=endpoint.api_specification_id,
            path=endpoint.path,
            method=endpoint.method.upper(),
            summary=endpoint.summary,
            description=endpoint.description,
            operation_id=endpoint.operation_id,
        )

        return self.repository.add(db, entity)

    def create(
        self,
        db: Session,
        endpoint: EndpointCreate,
    ) -> Endpoint:
        """
        Create a standalone endpoint.

        This method owns the transaction.
        """

        try:
            entity = self.create_entity(
                db,
                endpoint,
            )

            db.commit()
            db.refresh(entity)

            return entity

        except Exception:
            db.rollback()
            raise

    def create_many_entities(
        self,
        db: Session,
        endpoints: list[EndpointCreate],
    ) -> list[Endpoint]:
        """
        Create multiple endpoints inside the current transaction.

        This method does NOT commit or rollback.
        """

        created: list[Endpoint] = []

        for endpoint in endpoints:
            entity = self.create_entity(
                db,
                endpoint,
            )

            created.append(entity)

        return created

    def create_many(
        self,
        db: Session,
        endpoints: list[EndpointCreate],
    ) -> list[Endpoint]:
        """
        Create multiple endpoints as one standalone transaction.
        """

        try:
            created = self.create_many_entities(
                db,
                endpoints,
            )

            db.commit()

            for entity in created:
                db.refresh(entity)

            return created

        except Exception:
            db.rollback()
            raise

    def get(
        self,
        db: Session,
        endpoint_id: int,
    ) -> Endpoint | None:
        return self.repository.get_by_id(
            db,
            endpoint_id,
        )

    def list_by_specification(
        self,
        db: Session,
        specification_id: int,
    ) -> list[Endpoint]:
        return self.repository.get_by_specification(
            db,
            specification_id,
        )
