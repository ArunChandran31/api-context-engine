from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser
from app.database.models.endpoint import Endpoint
from app.rag.indexing_orchestrator import RAGIndexingOrchestrator
from app.schemas.api_specification import ApiSpecificationCreate
from app.schemas.endpoint import EndpointCreate
from app.schemas.upload import UploadRAGResponse, UploadResponse
from app.services.api_specification_service import ApiSpecificationService
from app.services.endpoint_service import EndpointService
from app.services.parser_service import ParserService


class UploadService:
    """
    Coordinates the complete OpenAPI ingestion workflow.

    Every uploaded specification belongs to the authenticated
    Supabase user.
    """

    def __init__(
        self,
        rag_indexing_orchestrator: RAGIndexingOrchestrator,
    ) -> None:
        self.parser_service = ParserService()
        self.specification_service = ApiSpecificationService()
        self.endpoint_service = EndpointService()
        self.rag_indexing_orchestrator = rag_indexing_orchestrator

    def upload(
        self,
        db: Session,
        content: bytes,
        filename: str,
        user: AuthenticatedUser | None = None,
    ) -> UploadResponse:
        """
        Parse and persist an OpenAPI specification.

        The specification and all endpoints are stored inside
        a single database transaction.
        """

        try:
            parsed = self.parser_service.parse(
                content=content,
                filename=filename,
            )

            specification_data = ApiSpecificationCreate(
                title=parsed.title,
                version=parsed.version,
                description=parsed.description,
                base_url=parsed.base_url,
                source_file=filename,
            )

            specification = self.specification_service.create_entity(
                db,
                specification_data,
                user,
            )

            db.flush()

            endpoints_data = [
                EndpointCreate(
                    api_specification_id=specification.id,
                    path=endpoint.path,
                    method=endpoint.method,
                    summary=endpoint.summary,
                    description=endpoint.description,
                    operation_id=endpoint.operation_id,
                    parameters=endpoint.parameters,
                    request_body=endpoint.request_body,
                    responses=endpoint.responses,
                    security=endpoint.security,
                )
                for endpoint in parsed.endpoints
            ]

            created_endpoints = self.endpoint_service.create_many_entities(
                db,
                endpoints_data,
            )

            db.commit()
            db.refresh(specification)

        except Exception:
            db.rollback()
            raise

        indexing_result = self.rag_indexing_orchestrator.index_specification(
            specification,
        )

        return UploadResponse(
            specification_id=specification.id,
            title=specification.title,
            version=specification.version,
            endpoints_created=len(created_endpoints),
            filename=filename,
            rag=UploadRAGResponse(
                documents_indexed=indexing_result.documents_indexed,
                chunks_indexed=indexing_result.chunks_indexed,
                cache_entries_invalidated=indexing_result.cache_entries_invalidated,
            ),
        )

    def replace(
        self,
        db: Session,
        specification_id: int,
        content: bytes,
        filename: str,
        user: AuthenticatedUser | None = None,
    ) -> UploadResponse:
        """
        Replace an existing specification.

        The specification MUST belong to the authenticated user.
        """

        try:
            specification = self.specification_service.get(
                db,
                specification_id,
                user,
            )

            if specification is None:
                raise ValueError(
                    f"API specification with ID {specification_id} was not found"
                )

            parsed = self.parser_service.parse(
                content=content,
                filename=filename,
            )

            specification.title = parsed.title
            specification.version = parsed.version
            specification.description = parsed.description
            specification.base_url = parsed.base_url
            specification.source_file = filename

            db.flush()

            db.execute(
                delete(Endpoint).where(
                    Endpoint.api_specification_id == specification_id,
                )
            )

            db.flush()

            endpoints_data = [
                EndpointCreate(
                    api_specification_id=specification_id,
                    path=endpoint.path,
                    method=endpoint.method,
                    summary=endpoint.summary,
                    description=endpoint.description,
                    operation_id=endpoint.operation_id,
                    parameters=endpoint.parameters,
                    request_body=endpoint.request_body,
                    responses=endpoint.responses,
                    security=endpoint.security,
                )
                for endpoint in parsed.endpoints
            ]

            created_endpoints = self.endpoint_service.create_many_entities(
                db,
                endpoints_data,
            )

            db.commit()
            db.refresh(specification)

        except Exception:
            db.rollback()
            raise

        indexing_result = self.rag_indexing_orchestrator.index_specification(
            specification,
        )

        return UploadResponse(
            specification_id=specification.id,
            title=specification.title,
            version=specification.version,
            endpoints_created=len(created_endpoints),
            filename=filename,
            rag=UploadRAGResponse(
                documents_indexed=indexing_result.documents_indexed,
                chunks_indexed=indexing_result.chunks_indexed,
                cache_entries_invalidated=(indexing_result.cache_entries_invalidated),
            ),
        )
