from sqlalchemy.orm import Session

from app.schemas.api_specification import ApiSpecificationCreate
from app.schemas.endpoint import EndpointCreate
from app.schemas.upload import UploadResponse
from app.services.api_specification_service import ApiSpecificationService
from app.services.endpoint_service import EndpointService
from app.services.parser_service import ParserService


class UploadService:
    """
    Coordinates the complete OpenAPI ingestion workflow.

    This service owns the database transaction for the
    complete upload operation.
    """

    def __init__(self):
        self.parser_service = ParserService()
        self.specification_service = ApiSpecificationService()
        self.endpoint_service = EndpointService()

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

            # --------------------------------------------------
            # 7. Return upload result
            # --------------------------------------------------

            return UploadResponse(
                specification_id=specification.id,
                title=specification.title,
                version=specification.version,
                endpoints_created=len(created_endpoints),
                filename=filename,
            )

        except Exception:
            db.rollback()
            raise
