import re

from app.ai.test_plan_models import (
    TestPlan,
    TestPlanCategory,
    TestPlanItem,
)
from app.rag.retrieval_service import RetrievalResult


class TestPlanBuilder:
    """
    Derives a grounded API test plan from retrieved API
    specification context.

    This component does not generate executable tests.
    It determines which test scenarios are actually supported
    by the documented API behavior.

    Grounding principles:

    - Documented API facts may be used directly.
    - Schema/type information does not constitute a concrete
      runtime value.
    - Missing runtime values must remain placeholders when
      the final test is generated.
    - A test scenario must be supported by an explicit API
      fact rather than general API-testing assumptions.
    """

    def build(
        self,
        endpoint: str,
        contexts: list[RetrievalResult],
        categories: list[TestPlanCategory] | None = None,
    ) -> TestPlan:
        if not endpoint.strip():
            raise ValueError("Endpoint cannot be empty.")

        context_text = "\n\n".join(
            result.content.strip() for result in contexts if result.content.strip()
        )

        if not context_text:
            return TestPlan(
                endpoint=endpoint.strip(),
                items=[
                    TestPlanItem(
                        category="happy",
                        description=(
                            "API context unavailable; no API-specific "
                            "test scenario can be established."
                        ),
                        grounded_facts=("No API context was retrieved.",),
                    )
                ],
            )

        selected_categories = categories or [
            "happy",
            "validation",
            "edge",
            "auth",
            "errors",
        ]

        items: list[TestPlanItem] = []

        if "happy" in selected_categories:
            items.extend(
                self._build_happy_items(
                    context=context_text,
                )
            )

        if "validation" in selected_categories:
            items.extend(
                self._build_validation_items(
                    context=context_text,
                )
            )

        if "edge" in selected_categories:
            items.extend(
                self._build_edge_items(
                    context=context_text,
                )
            )

        if "auth" in selected_categories:
            items.extend(
                self._build_auth_items(
                    context=context_text,
                )
            )

        if "errors" in selected_categories:
            items.extend(
                self._build_error_items(
                    context=context_text,
                )
            )

        if not items:
            items.append(
                TestPlanItem(
                    category="happy",
                    description=(
                        "No requested test category is supported "
                        "by the supplied API context."
                    ),
                    grounded_facts=("No matching documented behavior was found.",),
                )
            )

        return TestPlan(
            endpoint=endpoint.strip(),
            items=items,
        )

    # ------------------------------------------------------------------
    # HAPPY PATH
    # ------------------------------------------------------------------

    def _build_happy_items(
        self,
        context: str,
    ) -> list[TestPlanItem]:
        normalized = context.lower()

        if not self._contains_documented_status(
            context=normalized,
            status_code=200,
        ):
            return []

        request_fields = self._extract_documented_request_fields(
            context,
        )

        required_fields = self._extract_required_fields(
            context,
        )

        grounded_facts: list[str] = [
            "HTTP 200 response is documented.",
        ]

        if request_fields:
            grounded_facts.append(
                "Documented request fields: " + ", ".join(request_fields) + "."
            )

        if required_fields:
            grounded_facts.append(
                "Documented required request fields: "
                + ", ".join(required_fields)
                + "."
            )

        grounded_facts.append(
            "Concrete runtime values are not documented unless "
            "explicitly present in API context; use placeholders "
            "for unavailable runtime values."
        )

        grounded_facts.append(
            "Do not claim that a concrete resource exists unless "
            "the API context explicitly documents such a value."
        )

        return [
            TestPlanItem(
                category="happy",
                description=(
                    "Generate a successful request using only the "
                    "documented request structure and assert the "
                    "documented HTTP 200 response. Do not invent "
                    "concrete runtime values, resource identifiers, "
                    "response properties, or response-body values "
                    "that are not explicitly documented."
                ),
                grounded_facts=tuple(dict.fromkeys(grounded_facts)),
            )
        ]

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def _build_validation_items(
        self,
        context: str,
    ) -> list[TestPlanItem]:
        items: list[TestPlanItem] = []

        # --------------------------------------------------------------
        # Required-field validation
        #
        # Only fields explicitly listed inside an OpenAPI
        # "required" array are eligible for missing-field tests.
        # --------------------------------------------------------------

        required_fields = self._extract_required_fields(
            context,
        )

        for field in required_fields:
            items.append(
                TestPlanItem(
                    category="validation",
                    description=(
                        f"Test the request with explicitly required "
                        f"field '{field}' omitted. Use placeholders or "
                        f"other documented values for remaining request "
                        f"fields when concrete values are not documented. "
                        f"Do not test omission of fields that are not "
                        f"explicitly documented as required."
                    ),
                    grounded_facts=(
                        f"Field '{field}' is documented as required.",
                        "Only explicitly required fields may be tested "
                        "as missing required fields.",
                        "Concrete runtime values must not be invented.",
                    ),
                )
            )

        # --------------------------------------------------------------
        # Request-body type validation
        #
        # IMPORTANT:
        # _extract_documented_types() may return path parameters,
        # query parameters, and body properties.
        #
        # Type-validation tests here should target request-body
        # properties only. Path parameter type validation is a
        # separate concern and should not be automatically treated
        # as a request-body validation scenario.
        # --------------------------------------------------------------

        documented_body_types = self._extract_request_body_types(
            context,
        )

        for field, field_type in documented_body_types:
            items.append(
                TestPlanItem(
                    category="validation",
                    description=(
                        f"Test the documented request-body type "
                        f"constraint for '{field}' ({field_type}). "
                        f"Use a synthetic value only when it intentionally "
                        f"violates the documented type for validation "
                        f"testing. Do not invent additional validation "
                        f"constraints."
                    ),
                    grounded_facts=(
                        f"Request-body field '{field}' is documented "
                        f"as type '{field_type}'.",
                        "Synthetic invalid values may be used only "
                        "to intentionally violate the documented type.",
                        "Path parameters must not be converted into "
                        "request-body validation scenarios.",
                    ),
                )
            )

        return items

    # ------------------------------------------------------------------
    # EDGE CASES
    # ------------------------------------------------------------------

    def _build_edge_items(
        self,
        context: str,
    ) -> list[TestPlanItem]:
        """
        Generate edge-case plans only when explicit edge constraints
        are documented.

        Merely seeing words such as:
            enum
            format
            default
            nullable

        is not sufficient by itself to establish an edge case.

        Explicit constraints such as:
            minimum
            maximum
            exclusiveMinimum
            exclusiveMaximum
            minLength
            maxLength
            minItems
            maxItems
            pattern

        are treated as grounded edge-case constraints.
        """

        edge_constraints = self._extract_edge_constraints(
            context,
        )

        if not edge_constraints:
            return []

        grounded_facts = [
            "Explicit edge-related constraints are documented.",
            "Only documented edge constraints may be tested.",
        ]

        grounded_facts.extend(
            f"Documented edge constraint: {constraint}."
            for constraint in edge_constraints
        )

        return [
            TestPlanItem(
                category="edge",
                description=(
                    "Generate edge-case tests only for explicitly "
                    "documented constraints. Test the documented "
                    "minimum, maximum, length, pattern, collection "
                    "boundary, or equivalent constraint without "
                    "inferring additional boundary behavior."
                ),
                grounded_facts=tuple(dict.fromkeys(grounded_facts)),
            )
        ]

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def _build_auth_items(
        self,
        context: str,
    ) -> list[TestPlanItem]:
        normalized = context.lower()

        if "security:" not in normalized:
            return []

        security_facts: list[str] = [
            "Security requirements are documented.",
            "Only the documented authentication mechanism may be used.",
            "Concrete token values are not API facts unless explicitly " "documented.",
            "Use a token placeholder when a concrete token is unavailable.",
            "Do not invent authentication response statuses.",
            "Do not infer successful authentication behavior unless "
            "a corresponding success response is documented.",
        ]

        return [
            TestPlanItem(
                category="auth",
                description=(
                    "Verify that the documented authentication "
                    "mechanism is represented in the request. "
                    "If the API context does not provide a concrete "
                    "credential, use a placeholder rather than "
                    "inventing a token. Do not assert an authentication "
                    "response status unless that status is explicitly "
                    "documented."
                ),
                grounded_facts=tuple(security_facts),
            )
        ]

    # ------------------------------------------------------------------
    # DOCUMENTED HTTP ERRORS
    # ------------------------------------------------------------------

    def _build_error_items(
        self,
        context: str,
    ) -> list[TestPlanItem]:
        items: list[TestPlanItem] = []

        required_fields = self._extract_required_fields(
            context,
        )

        path_parameters = self._extract_path_parameters(
            context,
        )

        request_facts: list[str] = []

        for field in required_fields:
            request_facts.append(f"Request field '{field}' is documented as required.")

        for parameter_name, parameter_type in path_parameters:
            request_facts.append(
                f"Path parameter '{parameter_name}' is documented "
                f"as type '{parameter_type}'."
            )

        if path_parameters:
            request_facts.append(
                "The API context documents parameter types but does "
                "not necessarily provide concrete parameter values."
            )

        request_facts.append(
            "Use placeholders for undocumented concrete path "
            "parameters and request-body values."
        )

        request_facts.append(
            "Use a synthetic resource identifier only when it is "
            "needed to exercise a documented resource-not-found "
            "response such as HTTP 404."
        )

        for status_code, description in self._extract_error_responses(context):
            grounded_facts = [
                f"HTTP {status_code} is documented.",
                f"Documented error description: {description}.",
            ]

            grounded_facts.extend(request_facts)

            items.append(
                TestPlanItem(
                    category="errors",
                    description=(
                        f"Test the documented HTTP {status_code} "
                        f"response: {description}. Construct the "
                        f"request using only documented API structure. "
                        f"Use placeholders for runtime values that "
                        f"are not explicitly documented. Do not invent "
                        f"additional error conditions."
                    ),
                    grounded_facts=tuple(dict.fromkeys(grounded_facts)),
                )
            )

        return items

    # ------------------------------------------------------------------
    # REQUIRED FIELDS
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_required_fields(
        context: str,
    ) -> list[str]:
        """
        Extract required fields from the common serialized
        OpenAPI context representation.

        Only fields explicitly contained in a `"required": [...]`
        array are returned.
        """

        fields: list[str] = []

        marker_pattern = re.compile(
            r'["\']required["\']\s*:\s*\[',
            re.IGNORECASE,
        )

        for match in marker_pattern.finditer(context):
            start = match.end()

            end = context.find(
                "]",
                start,
            )

            if end == -1:
                continue

            block = context[start:end]

            fields.extend(
                re.findall(
                    r'["\']([^"\']+)["\']',
                    block,
                )
            )

        return list(dict.fromkeys(fields))

    # ------------------------------------------------------------------
    # DOCUMENTED TYPES
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_documented_types(
        context: str,
    ) -> list[tuple[str, str]]:
        """
        Extract flattened OpenAPI field/type pairs.

        This helper intentionally remains generic because it is also
        useful for identifying documented types outside request-body
        properties.
        """

        pattern = re.compile(
            r"""
            ["']?([A-Za-z_][A-Za-z0-9_-]*)["']?
            \s*:\s*
            \{
                (?:
                    [^{}]*
                )
                ["']type["']
                \s*:\s*
                ["']([^"']+)["']
                [^{}]*
            \}
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        matches = pattern.findall(
            context,
        )

        return list(
            dict.fromkeys(
                (
                    field,
                    field_type.lower(),
                )
                for field, field_type in matches
            )
        )

    # ------------------------------------------------------------------
    # REQUEST-BODY TYPES
    # ------------------------------------------------------------------

    @classmethod
    def _extract_request_body_types(
        cls,
        context: str,
    ) -> list[tuple[str, str]]:
        """
        Extract documented request-body property types.

        The extraction is intentionally scoped to the Request Body /
        schema / properties section so path parameter types do not
        automatically become validation scenarios.

        Supports context such as:

            Request Body:
            {
                "schema": {
                    "properties": {
                        "name": {
                            "type": "string"
                        }
                    }
                }
            }
        """

        request_body_block = cls._extract_request_body_block(
            context,
        )

        if not request_body_block:
            return []

        properties_block = cls._extract_properties_block(
            request_body_block,
        )

        if not properties_block:
            return []

        return cls._extract_documented_types(
            properties_block,
        )

    # ------------------------------------------------------------------
    # REQUEST-BODY BLOCK
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_request_body_block(
        context: str,
    ) -> str:
        """
        Extract the portion of context beginning at a Request Body
        marker.

        If no explicit Request Body marker exists, return an empty
        string rather than guessing that arbitrary schema fields
        belong to the request body.
        """

        match = re.search(
            r"request\s+body\s*:",
            context,
            re.IGNORECASE,
        )

        if not match:
            return ""

        start = match.end()

        section_markers = [
            r"\bresponses\s*:",
            r"\bsecurity\s*:",
            r"\bparameters\s*:",
        ]

        end_positions: list[int] = []

        for marker in section_markers:
            section_match = re.search(
                marker,
                context[start:],
                re.IGNORECASE,
            )

            if section_match:
                end_positions.append(start + section_match.start())

        end = min(
            end_positions,
            default=len(context),
        )

        return context[start:end]

    # ------------------------------------------------------------------
    # PROPERTIES BLOCK
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_properties_block(
        context: str,
    ) -> str:
        """
        Extract the object following a `properties` marker.

        The parser uses balanced-brace scanning rather than a single
        greedy regular expression so nested schema structures do not
        accidentally consume unrelated sections.
        """

        match = re.search(
            r'["\']?properties["\']?\s*:\s*\{',
            context,
            re.IGNORECASE,
        )

        if not match:
            return ""

        opening_brace = context.find(
            "{",
            match.start(),
        )

        if opening_brace == -1:
            return ""

        depth = 0

        for index in range(
            opening_brace,
            len(context),
        ):
            character = context[index]

            if character == "{":
                depth += 1

            elif character == "}":
                depth -= 1

                if depth == 0:
                    return context[opening_brace + 1 : index]

        return ""

    # ------------------------------------------------------------------
    # DOCUMENTED REQUEST FIELDS
    # ------------------------------------------------------------------

    @classmethod
    def _extract_documented_request_fields(
        cls,
        context: str,
    ) -> list[str]:
        fields = [
            field
            for field, _ in cls._extract_request_body_types(
                context,
            )
        ]

        required_fields = cls._extract_required_fields(
            context,
        )

        return list(dict.fromkeys(fields + required_fields))

    # ------------------------------------------------------------------
    # PATH PARAMETERS
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_path_parameters(
        context: str,
    ) -> list[tuple[str, str]]:
        """
        Extract path parameter names and their documented types.
        """

        parameters: list[tuple[str, str]] = []

        pattern = re.compile(
            r"""
            ["']name["']
            \s*:\s*
            ["']([^"']+)["']
            .*?
            ["']in["']
            \s*:\s*
            ["']path["']
            .*?
            ["']type["']
            \s*:\s*
            ["']([^"']+)["']
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        for match in pattern.finditer(
            context,
        ):
            parameters.append(
                (
                    match.group(1),
                    match.group(2).lower(),
                )
            )

        return list(dict.fromkeys(parameters))

    # ------------------------------------------------------------------
    # EDGE CONSTRAINTS
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_edge_constraints(
        context: str,
    ) -> list[str]:
        """
        Extract explicit schema constraints that justify edge-case
        testing.

        Merely finding a generic schema keyword such as `enum`,
        `format`, `default`, or `nullable` is not enough to establish
        an edge-case scenario.
        """

        constraint_patterns = [
            (
                r'["\']minimum["\']\s*:\s*([^,\}\]]+)',
                "minimum",
            ),
            (
                r'["\']maximum["\']\s*:\s*([^,\}\]]+)',
                "maximum",
            ),
            (
                r'["\']exclusiveMinimum["\']\s*:\s*([^,\}\]]+)',
                "exclusiveMinimum",
            ),
            (
                r'["\']exclusiveMaximum["\']\s*:\s*([^,\}\]]+)',
                "exclusiveMaximum",
            ),
            (
                r'["\']minLength["\']\s*:\s*([^,\}\]]+)',
                "minLength",
            ),
            (
                r'["\']maxLength["\']\s*:\s*([^,\}\]]+)',
                "maxLength",
            ),
            (
                r'["\']minItems["\']\s*:\s*([^,\}\]]+)',
                "minItems",
            ),
            (
                r'["\']maxItems["\']\s*:\s*([^,\}\]]+)',
                "maxItems",
            ),
            (
                r'["\']pattern["\']\s*:\s*["\']([^"\']+)["\']',
                "pattern",
            ),
        ]

        constraints: list[str] = []

        for pattern_text, label in constraint_patterns:
            pattern = re.compile(
                pattern_text,
                re.IGNORECASE,
            )

            for match in pattern.finditer(
                context,
            ):
                value = match.group(1).strip()

                constraints.append(f"{label}={value}")

        return list(dict.fromkeys(constraints))

    # ------------------------------------------------------------------
    # ERROR RESPONSES
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_error_responses(
        context: str,
    ) -> list[tuple[int, str]]:
        """
        Extract documented HTTP error responses.

        Supports common serialized OpenAPI context such as:

            "400": {
                "description": "Invalid product"
            }

            "404": {
                "description": "Product not found"
            }
        """

        pattern = re.compile(
            r"""
            ["']([45]\d{2})["']
            \s*:\s*
            \{
                .*?
                ["']description["']
                \s*:\s*
                ["']([^"']+)["']
                .*?
            \}
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        results: list[tuple[int, str]] = []

        for match in pattern.finditer(
            context,
        ):
            results.append(
                (
                    int(match.group(1)),
                    match.group(2).strip(),
                )
            )

        return list(dict.fromkeys(results))

    # ------------------------------------------------------------------
    # STATUS CODE HELPER
    # ------------------------------------------------------------------

    @staticmethod
    def _contains_documented_status(
        context: str,
        status_code: int,
    ) -> bool:
        """
        Determine whether an exact HTTP status code is documented.
        """

        return bool(
            re.search(
                rf'["\']{status_code}["\']',
                context,
            )
        )
