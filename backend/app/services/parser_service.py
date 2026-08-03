from app.exceptions import EmptyUploadError, SpecificationParseError
from app.parser.extractor import extract_specification
from app.parser.models import ParsedSpecification
from app.parser.parser import load_spec


class ParserService:
    """
    Application service responsible for parsing OpenAPI specifications.

    This service performs no database operations.
    """

    def parse(
        self,
        content: bytes,
        filename: str,
    ) -> ParsedSpecification:
        """
        Parse raw JSON/YAML content into a ParsedSpecification.

        Args:
            content: Raw uploaded file content.
            filename: Original uploaded filename.

        Returns:
            ParsedSpecification containing API metadata and endpoints.
        """

        if not content:
            raise EmptyUploadError("Uploaded file is empty.")

        specification = load_spec(content)

        if not isinstance(specification, dict):
            raise SpecificationParseError(
                f"Unable to parse '{filename}' as an OpenAPI specification."
            )

        return extract_specification(specification)
