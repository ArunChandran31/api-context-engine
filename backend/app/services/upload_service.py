from sqlalchemy import delete
from sqlalchemy.orm import Session

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

    This service owns the database transaction for the
    complete upload operation and triggers RAG indexing
    after the database transaction has successfully committed.
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
    ) -> UploadResponse:
        """
        Parse and persist an OpenAPI specification.

        The specification and all endpoints are stored
        inside a single database transaction.

        RAG indexing is triggered only after the database
        transaction has successfully committed.
        """

        try:
            # --------------------------------------------------
            # 1. Parse uploaded OpenAPI document
            # --------------------------------------------------

            parsed = self.parser_service.parse(
                content=content,
                filename=filename,
            )

            # --------------------------------------------------
            # 2. Build API specification schema
            # --------------------------------------------------

            specification_data = ApiSpecificationCreate(
                title=parsed.title,
                version=parsed.version,
                description=parsed.description,
                base_url=parsed.base_url,
                source_file=filename,
            )

            # --------------------------------------------------
            # 3. Create specification without committing
            # --------------------------------------------------

            specification = self.specification_service.create_entity(
                db,
                specification_data,
            )

            # Generate the specification ID without committing.
            db.flush()

            # --------------------------------------------------
            # 4. Convert parsed endpoints into DB schemas
            # --------------------------------------------------

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

            # --------------------------------------------------
            # 5. Create endpoints without committing
            # --------------------------------------------------

            created_endpoints = self.endpoint_service.create_many_entities(
                db,
                endpoints_data,
            )

            # --------------------------------------------------
            # 6. Commit complete Unit of Work
            # --------------------------------------------------

            db.commit()

            # Reload generated database values.
            db.refresh(specification)

        except Exception:
            db.rollback()
            raise

        # ------------------------------------------------------
        # 7. Index the committed specification in RAG
        # ------------------------------------------------------

        indexing_result = self.rag_indexing_orchestrator.index_specification(
            specification,
        )

        # ------------------------------------------------------
        # 8. Return upload result including RAG statistics
        # ------------------------------------------------------

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
    ) -> UploadResponse:
        """
        Replace an existing OpenAPI specification and all of its endpoints.

        The complete replacement is performed inside one database
        transaction. RAG indexing happens only after the transaction
        successfully commits.
        """

        try:
            # --------------------------------------------------
            # 1. Find existing specification
            # --------------------------------------------------

            specification = self.specification_service.get(
                db,
                specification_id,
            )

            if specification is None:
                raise ValueError(
                    f"API specification with ID {specification_id} was not found"
                )

            # --------------------------------------------------
            # 2. Parse replacement OpenAPI document
            # --------------------------------------------------

            parsed = self.parser_service.parse(
                content=content,
                filename=filename,
            )

            # --------------------------------------------------
            # 3. Update specification metadata
            # --------------------------------------------------

            specification.title = parsed.title
            specification.version = parsed.version
            specification.description = parsed.description
            specification.base_url = parsed.base_url
            specification.source_file = filename

            db.flush()

            # --------------------------------------------------
            # 4. Remove existing endpoints
            # --------------------------------------------------

            db.execute(
                delete(Endpoint).where(
                    Endpoint.api_specification_id == specification_id,
                )
            )

            db.flush()

            # --------------------------------------------------
            # 5. Create replacement endpoints
            # --------------------------------------------------

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

            # --------------------------------------------------
            # 6. Commit complete replacement transaction
            # --------------------------------------------------

            db.commit()

            db.refresh(specification)

        except Exception:
            db.rollback()
            raise

        # ------------------------------------------------------
        # 7. Re-index the committed specification
        # ------------------------------------------------------

        indexing_result = self.rag_indexing_orchestrator.index_specification(
            specification,
        )

        # ------------------------------------------------------
        # 8. Return replacement result
        # ------------------------------------------------------

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
