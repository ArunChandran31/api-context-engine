import json

from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.rag.models import RAGDocument


class ContextGenerator:
    """
    Generates semantic RAG documents from persisted API specifications.
    """

    def generate(
        self,
        specification: ApiSpecification,
    ) -> list[RAGDocument]:
        """
        Generate one RAG document for each endpoint in a specification.
        """

        documents: list[RAGDocument] = []

        for endpoint in specification.endpoints:
            documents.append(
                self._generate_endpoint_document(
                    specification=specification,
                    endpoint=endpoint,
                )
            )

        return documents

    def _generate_endpoint_document(
        self,
        specification: ApiSpecification,
        endpoint: Endpoint,
    ) -> RAGDocument:
        """
        Generate a semantic document describing a single API endpoint.
        """

        content = self._build_endpoint_content(
            specification=specification,
            endpoint=endpoint,
        )

        return RAGDocument(
            content=content,
            specification_id=specification.id,
            endpoint_id=endpoint.id,
            path=endpoint.path,
            method=endpoint.method.upper(),
            operation_id=endpoint.operation_id,
            metadata={
                "api_title": specification.title,
                "api_version": specification.version,
                "source_file": specification.source_file,
            },
        )

    def _build_endpoint_content(
        self,
        specification: ApiSpecification,
        endpoint: Endpoint,
    ) -> str:
        """
        Build deterministic human-readable semantic content for an endpoint.

        Rich OpenAPI metadata such as parameters, request bodies,
        responses, and security requirements is included so that
        downstream RAG retrieval has access to the complete endpoint
        context.
        """

        sections = [
            f"API: {specification.title}",
        ]

        if specification.version:
            sections.append(f"Version: {specification.version}")

        sections.append(f"Endpoint: {endpoint.method.upper()} {endpoint.path}")

        if endpoint.summary:
            sections.append(f"Summary: {endpoint.summary}")

        if endpoint.description:
            sections.append(f"Description: {endpoint.description}")

        if endpoint.operation_id:
            sections.append(f"Operation ID: {endpoint.operation_id}")

        if endpoint.parameters:
            sections.append(
                "Parameters:\n"
                + json.dumps(
                    endpoint.parameters,
                    indent=2,
                    sort_keys=True,
                )
            )

        if endpoint.request_body:
            sections.append(
                "Request Body:\n"
                + json.dumps(
                    endpoint.request_body,
                    indent=2,
                    sort_keys=True,
                )
            )

        if endpoint.responses:
            sections.append(
                "Responses:\n"
                + json.dumps(
                    endpoint.responses,
                    indent=2,
                    sort_keys=True,
                )
            )

        if endpoint.security:
            sections.append(
                "Security:\n"
                + json.dumps(
                    endpoint.security,
                    indent=2,
                    sort_keys=True,
                )
            )

        return "\n".join(sections)
