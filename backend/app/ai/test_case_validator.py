import json
import re
from typing import Any

from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationResult,
)


class TestCaseGroundingValidator:
    """
    Validates generated API test cases against the supplied
    API specification context.

    Grounding rules:

    1. HTTP status codes must be documented.
    2. Authentication scopes, permissions, and roles must be documented.
    3. Request fields must be documented.
    4. Placeholders such as <NAME> and <PRICE> are allowed.
    5. Positive-test concrete values must be documented.
    6. Validation tests may use synthetic values when they intentionally
       violate a documented field type.
    7. Enum values must be documented.
    8. Authentication tests may use synthetic token values.
    9. Documented 404 error tests may use synthetic resource identifiers.
    10. Documented-error tests may not invent ordinary request-body values.
    11. Response properties must be grounded in an explicitly documented
        response schema.
    12. Request-body schemas must never be treated as response schemas.
    """

    # ------------------------------------------------------------------
    # STATUS CODE PATTERNS
    # ------------------------------------------------------------------

    _STATUS_CODE_PATTERN = re.compile(
        r"""
        (?:
            \bstatus_code\b
            |
            \bstatus\b
            |
            \bresponse\.status\b
            |
            \bhttp\s+status\b
            |
            \bstatus\s+code\b
        )
        \s*
        (?:
            ==+
            |
            !=+
            |
            equals?
            |
            toBe\s*\(
            |
            is
            |
            should\s+be
        )
        \s*
        (\d{3})
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    _HTTP_STATUS_PATTERN = re.compile(
        r"\bHTTP\s+(\d{3})\b",
        re.IGNORECASE,
    )

    _NATURAL_LANGUAGE_STATUS_PATTERN = re.compile(
        r"""
        \b
        (?:
            return
            |
            returns
            |
            returned
            |
            receive
            |
            receives
            |
            received
            |
            respond
            |
            responds
            |
            responded
            |
            expect
            |
            expects
            |
            expected
        )
        (?:
            \s+with
            |
            \s+an?\s+HTTP
            |
            \s+HTTP
            |
            \s+status(?:\s+code)?\s+of
        )?
        \s*
        (\d{3})
        \b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # ------------------------------------------------------------------
    # AUTHENTICATION PATTERNS
    # ------------------------------------------------------------------

    _AUTH_SCOPE_PATTERN = re.compile(
        r"\b(?:scope|scopes|permission|permissions|role|roles)"
        r"\s*[:=]\s*[\"'`]([^\"'`]+)[\"'`]",
        re.IGNORECASE,
    )

    # ------------------------------------------------------------------
    # PLACEHOLDER
    # ------------------------------------------------------------------

    _PLACEHOLDER_PATTERN = re.compile(
        r"^<[^<>]+>$",
    )

    # ------------------------------------------------------------------
    # JSON / JAVASCRIPT OBJECT PATTERNS
    # ------------------------------------------------------------------

    _JSON_OBJECT_PATTERN = re.compile(
        r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}",
        re.DOTALL,
    )

    _JS_SEND_PATTERN = re.compile(
        r"\.send\s*\(\s*(\{.*?\})\s*\)",
        re.DOTALL | re.IGNORECASE,
    )

    _JS_FIELD_PATTERN = re.compile(
        r"""
        (?:
            ["'](?P<quoted_name>[^"']+)["']
            |
            (?P<bare_name>[A-Za-z_$][A-Za-z0-9_$-]*)
        )
        \s*:\s*
        (?P<value>
            "(?:\\.|[^"\\])*"
            |
            '(?:\\.|[^'\\])*'
            |
            `(?:\\.|[^`\\])*`
            |
            <[^<>]+>
            |
            -?\d+(?:\.\d+)?
            |
            true
            |
            false
            |
            null
            |
            undefined
        )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # ------------------------------------------------------------------
    # PATH PARAMETER PATTERNS
    # ------------------------------------------------------------------

    _ENDPOINT_TEMPLATE_PATTERN = re.compile(
        r"""
        \b
        (?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)
        \s+
        (?P<path>/[^\s"'`]+)
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    _PATH_REQUEST_PATTERN = re.compile(
        r"""
        (?:
            ["'`]
        )
        (?P<path>
            /
            [A-Za-z0-9._~:/${}<>-]+
        )
        (?:
            ["'`]
        )
        """,
        re.VERBOSE,
    )

    _PATH_PLACEHOLDER_PATTERN = re.compile(
        r"""
        (?:
            \{(?P<braced>[A-Za-z_][A-Za-z0-9_-]*)\}
            |
            :(?P<colon>[A-Za-z_][A-Za-z0-9_-]*)
            |
            <(?P<placeholder>[A-Za-z_][A-Za-z0-9_-]*)>
        )
        """,
        re.VERBOSE,
    )

    # ------------------------------------------------------------------
    # MAIN VALIDATION
    # ------------------------------------------------------------------

    def validate(
        self,
        result: TestCaseGenerationResult,
        context: str,
    ) -> TestCaseGenerationResult:
        """
        Validate generated test cases against API context.

        Raises ValueError when generated API behavior or concrete
        API request values cannot be grounded in the supplied context.
        """

        context_text = context.strip()

        if not context_text:
            raise ValueError(
                "Cannot validate generated test cases because " "API context is empty."
            )

        normalized_context = context_text.lower()

        validated_cases: list[GeneratedTestCase] = []

        for test_case in result.test_cases:
            self._validate_status_codes(
                description=test_case.description,
                context=normalized_context,
            )

            self._validate_auth_scopes(
                description=test_case.description,
                context=normalized_context,
            )

            self._validate_path_parameters(
                description=test_case.description,
                context=context_text,
                category=test_case.category,
            )

            self._validate_response_grounding(
                description=test_case.description,
                context=context_text,
                category=test_case.category,
            )

            self._validate_request_values(
                description=test_case.description,
                context=context_text,
                category=test_case.category,
            )

            validated_cases.append(test_case)

        return TestCaseGenerationResult(
            test_cases=validated_cases,
        )

    # ------------------------------------------------------------------
    # STATUS CODES
    # ------------------------------------------------------------------

    def _validate_status_codes(
        self,
        description: str,
        context: str,
    ) -> None:
        """
        Reject explicitly referenced HTTP status codes that are not
        documented by the API.

        Supports both executable assertions and natural-language
        descriptions.
        """

        status_codes: set[str] = set()

        for match in self._STATUS_CODE_PATTERN.finditer(description):
            status_codes.add(match.group(1))

        for match in self._HTTP_STATUS_PATTERN.finditer(description):
            status_codes.add(match.group(1))

        for match in self._NATURAL_LANGUAGE_STATUS_PATTERN.finditer(description):
            status_codes.add(match.group(1))

        for status_code in status_codes:
            if status_code not in context:
                raise ValueError(
                    "Generated test case references undocumented "
                    f"HTTP status code {status_code}."
                )

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def _validate_auth_scopes(
        self,
        description: str,
        context: str,
    ) -> None:
        """
        Reject explicitly named authentication scopes,
        permissions, or roles that are not documented in the API context.
        """

        for match in self._AUTH_SCOPE_PATTERN.finditer(description):
            value = match.group(1).strip().lower()

            if value and value not in context:
                raise ValueError(
                    "Generated test case references an undocumented "
                    f"authentication permission or scope: {value}."
                )

    # ------------------------------------------------------------------
    # PATH PARAMETERS
    # ------------------------------------------------------------------

    def _validate_path_parameters(
        self,
        description: str,
        context: str,
        category: str,
    ) -> None:
        """
        Validate concrete path-parameter values separately from
        request-body values.
        """

        category_flags = self._category_flags(category)

        endpoint_templates = self._extract_endpoint_templates(
            context=context,
        )

        if not endpoint_templates:
            return

        request_paths = self._extract_request_paths(
            description=description,
        )

        if not request_paths:
            return

        allow_synthetic_resource_ids = category_flags[
            "errors"
        ] and self._context_documents_404(context)

        for request_path in request_paths:
            matching_template = self._find_matching_endpoint_template(
                request_path=request_path,
                endpoint_templates=endpoint_templates,
            )

            if matching_template is None:
                continue

            self._validate_path_against_template(
                request_path=request_path,
                endpoint_template=matching_template,
                context=context,
                allow_synthetic_resource_ids=allow_synthetic_resource_ids,
            )

    def _extract_endpoint_templates(
        self,
        context: str,
    ) -> list[str]:
        """
        Extract documented endpoint templates such as:

            POST /products/{product_id}
            GET /users/{user_id}
        """

        templates: list[str] = []

        for match in self._ENDPOINT_TEMPLATE_PATTERN.finditer(context):
            path = match.group("path").strip()

            if path not in templates:
                templates.append(path)

        return templates

    def _extract_request_paths(
        self,
        description: str,
    ) -> list[str]:
        """
        Extract literal request paths from generated test code.
        """

        paths: list[str] = []

        for match in self._PATH_REQUEST_PATTERN.finditer(description):
            path = match.group("path").strip()

            if not path.startswith("/"):
                continue

            if path not in paths:
                paths.append(path)

        return paths

    def _find_matching_endpoint_template(
        self,
        request_path: str,
        endpoint_templates: list[str],
    ) -> str | None:
        """
        Find the documented endpoint template corresponding to a
        generated request path.
        """

        request_segments = self._split_path(request_path)

        for template in endpoint_templates:
            template_segments = self._split_path(template)

            if len(request_segments) != len(template_segments):
                continue

            matches = True

            for request_segment, template_segment in zip(
                request_segments,
                template_segments,
            ):
                if self._is_path_parameter(template_segment):
                    continue

                if request_segment != template_segment:
                    matches = False
                    break

            if matches:
                return template

        return None

    @staticmethod
    def _split_path(path: str) -> list[str]:
        """
        Split a URL path into non-empty path segments.
        """

        return [segment for segment in path.split("/") if segment]

    def _is_path_parameter(
        self,
        segment: str,
    ) -> bool:
        """
        Return True when an endpoint segment represents a path
        parameter.
        """

        return bool(
            self._PATH_PLACEHOLDER_PATTERN.fullmatch(
                segment.strip(),
            )
        )

    def _get_path_parameter_name(
        self,
        segment: str,
    ) -> str | None:
        """
        Extract the documented path parameter name.
        """

        match = self._PATH_PLACEHOLDER_PATTERN.fullmatch(
            segment.strip(),
        )

        if not match:
            return None

        return (
            match.group("braced") or match.group("colon") or match.group("placeholder")
        )

    def _validate_path_against_template(
        self,
        request_path: str,
        endpoint_template: str,
        context: str,
        allow_synthetic_resource_ids: bool,
    ) -> None:
        """
        Validate each concrete value occupying a documented path
        parameter position.
        """

        request_segments = self._split_path(request_path)
        template_segments = self._split_path(endpoint_template)

        for request_segment, template_segment in zip(
            request_segments,
            template_segments,
        ):
            if not self._is_path_parameter(template_segment):
                continue

            parameter_name = self._get_path_parameter_name(
                template_segment,
            )

            if parameter_name is None:
                continue

            if self._is_placeholder(request_segment):
                continue

            if request_segment.startswith(":") and request_segment[1:].strip():
                continue

            if request_segment.startswith("${") and request_segment.endswith("}"):
                continue

            if allow_synthetic_resource_ids:
                continue

            normalized_context = context.lower()
            normalized_value = request_segment.lower()

            if request_path.lower() in normalized_context:
                continue

            escaped_parameter = re.escape(parameter_name)
            escaped_value = re.escape(normalized_value)

            parameter_value_patterns = [
                rf"""
                \b{escaped_parameter}\b
                \s*
                (?:
                    :
                    |
                    =
                    |
                    =>
                )
                \s*
                ["'`]?
                {escaped_value}
                ["'`]?
                \b
                """,
                rf"""
                ["'`]?{escaped_parameter}["'`]?
                \s*:\s*
                ["'`]?
                {escaped_value}
                ["'`]?
                (?:\s*[,}}\]])
                """,
            ]

            documented_as_parameter_value = any(
                re.search(
                    pattern,
                    normalized_context,
                    re.IGNORECASE | re.VERBOSE,
                )
                for pattern in parameter_value_patterns
            )

            if documented_as_parameter_value:
                continue

            raise ValueError(
                "Generated test case contains an undocumented "
                f"concrete path parameter value for "
                f"'{parameter_name}': {request_segment}."
            )

    def _context_documents_404(
        self,
        context: str,
    ) -> bool:
        """
        Return True when HTTP 404 is explicitly documented.
        """

        normalized_context = context.lower()

        if re.search(
            r"\bhttp\s+404\b",
            normalized_context,
        ):
            return True

        if re.search(
            r"\bstatus(?:_code|\s+code)?\s*(?:==|=|:|is|of)?\s*404\b",
            normalized_context,
        ):
            return True

        return bool(
            re.search(
                r"\b(?:returns?|responds?|responded|expects?|expected)"
                r"(?:\s+with)?(?:\s+an?\s+http)?\s+404\b",
                normalized_context,
            )
        )

    # ------------------------------------------------------------------
    # REQUEST VALUES
    # ------------------------------------------------------------------

    def _validate_request_values(
        self,
        description: str,
        context: str,
        category: str,
    ) -> None:
        """
        Validate request-body values.
        """

        category_flags = self._category_flags(category)

        javascript_objects = self._extract_javascript_objects(
            description,
        )

        for javascript_object in javascript_objects:
            self._validate_javascript_object(
                value=javascript_object,
                context=context,
                allow_synthetic_invalid_values=category_flags["validation"],
                allow_synthetic_values=category_flags["auth"],
            )

        if not javascript_objects:
            json_objects = self._extract_json_objects(
                description,
            )

            for json_object in json_objects:
                self._validate_json_object(
                    value=json_object,
                    context=context,
                    allow_synthetic_invalid_values=category_flags["validation"],
                    allow_synthetic_values=category_flags["auth"],
                )

    # ------------------------------------------------------------------
    # RESPONSE BODY GROUNDING
    # ------------------------------------------------------------------

    _RESPONSE_PROPERTY_PATTERNS = (
        re.compile(
            r"\bresponse\s*\.\s*body\s*\.\s*" r"([A-Za-z_$][A-Za-z0-9_$-]*)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bresponse\s*\.\s*body\s*\[\s*['\"]" r"([^'\"]+)['\"]\s*\]",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bresponse\s*\.\s*body\s*\)\s*\.\s*"
            r"toHaveProperty\s*\(\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bresponse\s*\.\s*body\s*\.\s*"
            r"toHaveProperty\s*\(\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE,
        ),
    )

    _RESPONSE_BODY_ASSERTION_PATTERN = re.compile(
        r"\b(?:expect\s*\(\s*)?" r"response\s*\.\s*body\s*(?:\)|\.|\[)",
        re.IGNORECASE,
    )

    _RESPONSE_SCHEMA_MARKERS = re.compile(
        r"\b(?:response\s+body|response\s+schema)\b",
        re.IGNORECASE,
    )

    def _validate_response_grounding(
        self,
        description: str,
        context: str,
        category: str,
    ) -> None:
        """
        Validate response-body assertions against documented response
        schemas.

        Response properties are never inferred from request-body schemas.

        A response property must either:

        1. be explicitly documented in a response-body schema, or
        2. be rejected as ungrounded.

        A documented status code alone is insufficient.
        """

        response_properties = self._extract_response_properties_from_description(
            description,
        )

        response_body_referenced = bool(
            self._RESPONSE_BODY_ASSERTION_PATTERN.search(
                description,
            )
        )

        has_response_body_assertion = bool(
            response_properties or response_body_referenced
        )

        category_flags = self._category_flags(category)
        normalized_category = category.lower()

        # --------------------------------------------------------------
        # EDGE CASE: OPTIONAL FIELD OMISSION
        # --------------------------------------------------------------

        if (
            not category_flags["errors"]
            and "edge" in normalized_category
            and self._describes_optional_field_omission(description)
        ):
            success_statuses = {
                status_code
                for status_code in self._extract_status_codes_from_description(
                    description,
                )
                if 200 <= int(status_code) < 300
            }

            for status_code in success_statuses:
                if not self._context_documents_optional_omission_success(
                    context=context,
                    status_code=status_code,
                ):
                    raise ValueError(
                        "Generated edge test infers an undocumented "
                        f"successful response HTTP {status_code} from "
                        "optional-field omission."
                    )

        if not has_response_body_assertion:
            return

        # --------------------------------------------------------------
        # DETERMINE THE ASSERTED STATUS
        # --------------------------------------------------------------

        asserted_statuses = self._extract_status_codes_from_description(
            description,
        )

        # --------------------------------------------------------------
        # RESPONSE SCHEMA EXTRACTION
        # --------------------------------------------------------------

        documented_response_properties = (
            self._extract_documented_response_properties_for_status(
                context=context,
                status_codes=asserted_statuses,
            )
        )

        # --------------------------------------------------------------
        # NO DOCUMENTED RESPONSE SCHEMA
        # --------------------------------------------------------------

        if not documented_response_properties:
            raise ValueError(
                "Generated test case asserts a response property, but no "
                "response schema is documented."
            )

        # --------------------------------------------------------------
        # RESPONSE PROPERTY GROUNDING
        # --------------------------------------------------------------

        for property_name in response_properties:
            normalized_name = property_name.strip().lower()

            if normalized_name not in documented_response_properties:
                raise ValueError(
                    "Generated test case references an undocumented "
                    f"response property: {property_name}."
                )

    @classmethod
    def _extract_response_properties_from_description(
        cls,
        description: str,
    ) -> list[str]:
        """
        Extract properties explicitly accessed on response.body.
        """

        properties: list[str] = []

        for pattern in cls._RESPONSE_PROPERTY_PATTERNS:
            for match in pattern.finditer(description):
                property_name = match.group(1).strip()

                if property_name and property_name not in properties:
                    properties.append(property_name)

        return properties

    @classmethod
    def _extract_status_codes_from_description(
        cls,
        description: str,
    ) -> set[str]:
        """
        Extract HTTP status codes explicitly asserted or described.
        """

        if not description:
            return set()

        status_codes: set[str] = set()

        status_codes.update(
            re.findall(
                r"""
                \bexpect
                \s*\(
                    \s*
                    (?:response|res)
                    \s*\.\s*
                    (?:status|status_code)
                    \s*
                \)
                \s*\.\s*
                (?:toBe|toEqual|toStrictEqual)
                \s*\(
                    \s*
                    (?P<code>[1-5][0-9]{2})
                    \s*
                \)
                """,
                description,
                flags=re.IGNORECASE | re.VERBOSE,
            )
        )

        status_codes.update(
            re.findall(
                r"""
                \b(?:response|res)
                \s*\.\s*
                (?:status|status_code)
                \s*
                (?:===|==|!==|!=)
                \s*
                (?P<code>[1-5][0-9]{2})
                """,
                description,
                flags=re.IGNORECASE | re.VERBOSE,
            )
        )

        status_codes.update(
            re.findall(
                r"""
                \bHTTP
                \s*
                (?P<code>[1-5][0-9]{2})
                \b
                """,
                description,
                flags=re.IGNORECASE | re.VERBOSE,
            )
        )

        status_codes.update(
            re.findall(
                r"""
                \b
                (?:
                    returns
                    |
                    return
                    |
                    responds?\s+with
                    |
                    receives?
                    |
                    receive
                    |
                    expects?
                    |
                    expect
                    |
                    gets?
                    |
                    get
                )
                \s+
                (?P<code>[1-5][0-9]{2})
                \b
                """,
                description,
                flags=re.IGNORECASE | re.VERBOSE,
            )
        )

        return set(status_codes)

    # ------------------------------------------------------------------
    # RESPONSE SCHEMA EXTRACTION
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_balanced_object(
        text: str,
        opening_index: int,
    ) -> str | None:
        """
        Return a balanced {...} object beginning at opening_index.
        """

        if opening_index < 0 or opening_index >= len(text):
            return None

        if text[opening_index] != "{":
            return None

        depth = 0
        in_string = False
        string_quote = ""
        escaped = False

        for index in range(opening_index, len(text)):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == string_quote:
                    in_string = False

                continue

            if char in {"'", '"', "`"}:
                in_string = True
                string_quote = char
                continue

            if char == "{":
                depth += 1

            elif char == "}":
                depth -= 1

                if depth == 0:
                    return text[opening_index : index + 1]

        return None

    @classmethod
    def _extract_documented_response_properties_for_status(
        cls,
        context: str,
        status_codes: set[str],
    ) -> set[str]:
        """
        Extract response properties only from the explicitly asserted
        response status.

        For example:

            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "id": {
                                    "type": "integer"
                                }
                            }
                        }
                    }
                }
            }

        A request-body `properties` block is never considered a response
        schema.
        """

        properties: set[str] = set()

        normalized = context

        status_object_pattern = re.compile(
            r"""
            [\"'](?P<status>\d{3})[\"']
            \s*:\s*
            \{
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        matches = list(
            status_object_pattern.finditer(normalized),
        )

        for match in matches:
            status = match.group("status")

            if status_codes and status not in status_codes:
                continue

            opening = normalized.find(
                "{",
                match.start(),
                match.end(),
            )

            block = cls._extract_balanced_object(
                normalized,
                opening,
            )

            if not block:
                continue

            # A response object must contain an actual response schema
            # marker. A plain description such as:
            #
            #   "200": {"description": "Success"}
            #
            # is not sufficient.
            if not re.search(
                r"\b(?:schema|content)\b",
                block,
                re.IGNORECASE,
            ):
                continue

            properties.update(
                cls._extract_properties_from_response_schema(
                    block,
                )
            )

        # If no explicit status was asserted, retain support for flattened
        # response documentation.
        if not status_codes:
            properties.update(
                cls._extract_documented_response_properties(
                    context,
                )
            )

        return {value.lower() for value in properties}

    @classmethod
    def _extract_documented_response_properties(
        cls,
        context: str,
    ) -> set[str]:
        """
        Extract response properties from explicitly response-related
        regions.

        This method intentionally does not treat arbitrary `properties`
        blocks as response schemas.
        """

        normalized = context
        properties: set[str] = set()

        status_object_pattern = re.compile(
            r"""
            [\"'](?P<status>\d{3})[\"']
            \s*:\s*
            \{
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        for match in status_object_pattern.finditer(normalized):
            opening = normalized.find(
                "{",
                match.start(),
                match.end(),
            )

            block = cls._extract_balanced_object(
                normalized,
                opening,
            )

            if not block:
                continue

            if not re.search(
                r"\b(?:schema|content)\b",
                block,
                re.IGNORECASE,
            ):
                continue

            properties.update(
                cls._extract_properties_from_response_schema(
                    block,
                )
            )

        response_markers = list(
            re.finditer(
                r"\b(?:response\s+body|response\s+schema)\b",
                normalized,
                re.IGNORECASE,
            )
        )

        for marker_index, marker in enumerate(response_markers):
            region_start = marker.start()

            if marker_index + 1 < len(response_markers):
                region_end = response_markers[marker_index + 1].start()
            else:
                region_end = len(normalized)

            region = normalized[region_start:region_end]

            properties.update(
                cls._extract_properties_from_schema_block(
                    region,
                )
            )

        return {value.lower() for value in properties}

    @classmethod
    def _extract_properties_from_response_schema(
        cls,
        block: str,
    ) -> set[str]:
        """
        Extract properties from an actual response schema.

        The implementation handles nested OpenAPI-style structures such as:

            content
              -> application/json
                -> schema
                  -> properties
                    -> id
        """

        properties: set[str] = set()

        schema_matches = list(
            re.finditer(
                r"[\"']schema[\"']\s*:\s*\{",
                block,
                re.IGNORECASE,
            )
        )

        for schema_match in schema_matches:
            opening = block.find(
                "{",
                schema_match.start(),
                schema_match.end(),
            )

            schema_block = cls._extract_balanced_object(
                block,
                opening,
            )

            if not schema_block:
                continue

            properties.update(
                cls._extract_properties_from_schema_block(
                    schema_block,
                )
            )

        # Also support a flattened response schema representation:
        #
        # Response Body:
        #   properties:
        #     id:
        # type: integer
        #
        if not schema_matches:
            properties.update(
                cls._extract_properties_from_schema_block(
                    block,
                )
            )

        return properties

    @classmethod
    def _extract_properties_from_schema_block(
        cls,
        block: str,
    ) -> set[str]:
        """
        Extract field names from a schema properties block.
        """

        properties: set[str] = set()

        properties_marker = re.compile(
            r"""
            [\"']?properties[\"']?
            \s*:\s*
            \{
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        for match in properties_marker.finditer(block):
            opening = block.find(
                "{",
                match.start(),
                match.end(),
            )

            properties_object = cls._extract_balanced_object(
                block,
                opening,
            )

            if not properties_object:
                continue

            # JSON/OpenAPI:
            #
            # "id": {
            #     "type": "integer"
            # }
            for field_match in re.finditer(
                r"""
                [\"']([^\"']+)[\"']
                \s*:\s*
                \{
                """,
                properties_object,
                re.IGNORECASE | re.VERBOSE,
            ):
                properties.add(field_match.group(1))

            # Flattened:
            #
            # id:
            # type: integer
            for field_match in re.finditer(
                r"""
                (?:^|\n)
                \s*
                ([A-Za-z_$][A-Za-z0-9_$-]*)
                \s*:\s*
                (?:
                    type\s*:\s*
                    |
                    \{\s*type\s*:\s*
                )
                """,
                properties_object,
                re.IGNORECASE | re.VERBOSE,
            ):
                properties.add(field_match.group(1))

        # Direct JSON-like property declaration.
        for match in re.finditer(
            r"""
            [\"']([^\"']+)[\"']
            \s*:\s*
            \{
                \s*
                [\"']type[\"']
                \s*:
            """,
            block,
            re.IGNORECASE | re.VERBOSE,
        ):
            properties.add(match.group(1))

        return properties

    # ------------------------------------------------------------------
    # OPTIONAL FIELD OMISSION
    # ------------------------------------------------------------------

    @staticmethod
    def _describes_optional_field_omission(
        description: str,
    ) -> bool:
        """
        Detect generated tests that explicitly describe omission of an
        optional request field.
        """

        normalized = re.sub(
            r"\s+",
            " ",
            description.lower(),
        )

        has_optional = bool(
            re.search(
                r"\boptional\b",
                normalized,
                re.IGNORECASE,
            )
        )

        has_omission = bool(
            re.search(
                r"\b(?:omit|omits|omitted|omitting|missing|absence)\b",
                normalized,
                re.IGNORECASE,
            )
        )

        return has_optional and has_omission

    @staticmethod
    def _context_documents_optional_omission_success(
        context: str,
        status_code: str,
    ) -> bool:
        """
        Return True only when the API documentation explicitly connects
        optional-field omission with the asserted success status.
        """

        normalized = re.sub(
            r"\s+",
            " ",
            context.lower(),
        )

        omission_pattern = re.compile(
            r"\b(?:optional|omit|omitted|omitting|missing|absence)\b",
            re.IGNORECASE,
        )

        status_pattern = re.compile(
            rf"\b(?:http\s+)?{re.escape(status_code)}\b",
            re.IGNORECASE,
        )

        omission_matches = list(
            omission_pattern.finditer(
                normalized,
            )
        )

        if not omission_matches:
            return False

        for omission_match in omission_matches:
            start = max(
                0,
                omission_match.start() - 300,
            )

            end = min(
                len(normalized),
                omission_match.end() + 300,
            )

            region = normalized[start:end]

            if status_pattern.search(region):
                return True

        return False

    # ------------------------------------------------------------------
    # OBJECT EXTRACTION
    # ------------------------------------------------------------------

    def _extract_json_objects(
        self,
        description: str,
    ) -> list[str]:
        """
        Extract JSON-like objects from generated output.
        """

        return self._JSON_OBJECT_PATTERN.findall(
            description,
        )

    def _extract_javascript_objects(
        self,
        description: str,
    ) -> list[str]:
        """
        Extract JavaScript / TypeScript objects passed to .send({...}).
        """

        return [
            match.group(1)
            for match in self._JS_SEND_PATTERN.finditer(
                description,
            )
        ]

    # ------------------------------------------------------------------
    # JSON OBJECT VALIDATION
    # ------------------------------------------------------------------

    def _validate_json_object(
        self,
        value: str,
        context: str,
        allow_synthetic_invalid_values: bool,
        allow_synthetic_values: bool,
    ) -> None:
        """
        Validate a strict JSON request object.
        """

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return

        if not isinstance(parsed, dict):
            return

        for field_name, field_value in parsed.items():
            if not isinstance(field_name, str):
                continue

            self._validate_field(
                field_name=field_name,
                field_value=field_value,
                context=context,
                allow_synthetic_invalid_values=(allow_synthetic_invalid_values),
                allow_synthetic_values=allow_synthetic_values,
            )

    # ------------------------------------------------------------------
    # JAVASCRIPT OBJECT VALIDATION
    # ------------------------------------------------------------------

    def _validate_javascript_object(
        self,
        value: str,
        context: str,
        allow_synthetic_invalid_values: bool,
        allow_synthetic_values: bool,
    ) -> None:
        """
        Validate a JavaScript / TypeScript object literal.
        """

        for match in self._JS_FIELD_PATTERN.finditer(value):
            field_name = match.group("quoted_name") or match.group("bare_name")

            raw_value = match.group("value")

            if not field_name or not raw_value:
                continue

            field_value = self._parse_javascript_value(
                raw_value,
            )

            self._validate_field(
                field_name=field_name,
                field_value=field_value,
                context=context,
                allow_synthetic_invalid_values=(allow_synthetic_invalid_values),
                allow_synthetic_values=allow_synthetic_values,
            )

    def _parse_javascript_value(
        self,
        raw_value: str,
    ) -> Any:
        """
        Convert a simple JavaScript literal into a Python value.
        """

        value = raw_value.strip()

        if self._is_placeholder(value):
            return value

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"', "`"}:
            return value[1:-1]

        if value.lower() == "true":
            return True

        if value.lower() == "false":
            return False

        if value.lower() == "null":
            return None

        if value.lower() == "undefined":
            return "__UNDEFINED__"

        try:
            if "." in value:
                return float(value)

            return int(value)

        except ValueError:
            return value

    # ------------------------------------------------------------------
    # FIELD VALIDATION
    # ------------------------------------------------------------------

    def _validate_field(
        self,
        field_name: str,
        field_value: Any,
        context: str,
        allow_synthetic_invalid_values: bool,
        allow_synthetic_values: bool,
    ) -> None:
        """
        Validate one request field.
        """

        self._validate_field_name(
            field_name=field_name,
            context=context,
        )

        if isinstance(field_value, str) and self._is_placeholder(field_value):
            return

        expected_type = self._get_field_type(
            field_name=field_name,
            context=context,
        )

        enum_values = self._get_enum_values(
            field_name=field_name,
            context=context,
        )

        if isinstance(field_value, str):

            if (
                allow_synthetic_invalid_values
                and expected_type is not None
                and expected_type != "string"
            ):
                return

            if enum_values:
                self._validate_enum_value(
                    field_name=field_name,
                    field_value=field_value,
                    enum_values=enum_values,
                )
                return

            if allow_synthetic_values:
                self._validate_string_type(
                    field_name=field_name,
                    field_value=field_value,
                    expected_type=expected_type,
                )
                return

            self._validate_concrete_value(
                field_name=field_name,
                field_value=field_value,
                context=context,
            )

            return

        if isinstance(field_value, bool):

            if (
                allow_synthetic_invalid_values
                and expected_type is not None
                and expected_type != "boolean"
            ):
                return

            if allow_synthetic_values:
                self._validate_boolean_type(
                    field_name=field_name,
                    expected_type=expected_type,
                )
                return

            self._validate_concrete_value(
                field_name=field_name,
                field_value=field_value,
                context=context,
            )

            return

        if isinstance(field_value, (int, float)) and not isinstance(field_value, bool):

            if (
                allow_synthetic_invalid_values
                and expected_type is not None
                and expected_type not in {"number", "integer"}
            ):
                return

            if allow_synthetic_values:
                self._validate_numeric_type(
                    field_name=field_name,
                    field_value=field_value,
                    expected_type=expected_type,
                )
                return

            self._validate_concrete_value(
                field_name=field_name,
                field_value=field_value,
                context=context,
            )

            return

        if field_value is None:

            if allow_synthetic_invalid_values:
                return

            if "null" not in context.lower():
                raise ValueError(
                    "Generated test case contains an undocumented "
                    f"null value for request field '{field_name}'."
                )

            return

        if field_value == "__UNDEFINED__":

            if allow_synthetic_invalid_values:
                return

            raise ValueError(
                "Generated test case contains an undocumented "
                f"undefined value for request field '{field_name}'."
            )

        if isinstance(field_value, list):

            for item in field_value:
                self._validate_field(
                    field_name=field_name,
                    field_value=item,
                    context=context,
                    allow_synthetic_invalid_values=(allow_synthetic_invalid_values),
                    allow_synthetic_values=allow_synthetic_values,
                )

            return

        if isinstance(field_value, dict):

            for nested_name, nested_value in field_value.items():
                self._validate_field(
                    field_name=nested_name,
                    field_value=nested_value,
                    context=context,
                    allow_synthetic_invalid_values=(allow_synthetic_invalid_values),
                    allow_synthetic_values=allow_synthetic_values,
                )

    # ------------------------------------------------------------------
    # FIELD NAME
    # ------------------------------------------------------------------

    def _validate_field_name(
        self,
        field_name: str,
        context: str,
    ) -> None:
        """
        Ensure the request field exists in API context.
        """

        if field_name.lower() not in context.lower():
            raise ValueError(
                "Generated test case references an undocumented "
                f"request field: {field_name}."
            )

    # ------------------------------------------------------------------
    # FIELD TYPE
    # ------------------------------------------------------------------

    def _get_field_type(
        self,
        field_name: str,
        context: str,
    ) -> str | None:
        """
        Extract the documented OpenAPI type for a field.
        """

        pattern = re.compile(
            rf"""
            ["']?{re.escape(field_name)}["']?
            \s*:\s*
            \{{\s*
            (?:
                [^{{}}]*
            )
            ["']type["']
            \s*:\s*
            ["']([^"']+)["']
            [^{{}}]*
            \}}
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        match = pattern.search(context)

        if match:
            return match.group(1).lower()

        return None

    # ------------------------------------------------------------------
    # ENUM VALUES
    # ------------------------------------------------------------------

    def _get_enum_values(
        self,
        field_name: str,
        context: str,
    ) -> list[str]:
        """
        Extract documented enum values for a field.
        """

        pattern = re.compile(
            rf"""
            ["']?{re.escape(field_name)}["']?
            \s*:\s*
            \{{\s*
            (?:
                [^{{}}]*
            )
            ["']enum["']
            \s*:\s*
            \[
                (.*?)
            \]
            [^{{}}]*
            \}}
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        match = pattern.search(context)

        if not match:
            return []

        enum_block = match.group(1)

        return re.findall(
            r'["\']([^"\']+)["\']',
            enum_block,
        )

    def _validate_enum_value(
        self,
        field_name: str,
        field_value: str,
        enum_values: list[str],
    ) -> None:
        """
        Ensure a concrete enum value is documented.
        """

        normalized_value = field_value.lower()
        normalized_enums = {value.lower() for value in enum_values}

        if normalized_value not in normalized_enums:
            raise ValueError(
                "Generated test case contains an undocumented "
                f"concrete value for request field "
                f"'{field_name}': {field_value}."
            )

    # ------------------------------------------------------------------
    # SYNTHETIC VALUE TYPE VALIDATION
    # ------------------------------------------------------------------

    def _validate_string_type(
        self,
        field_name: str,
        field_value: str,
        expected_type: str | None,
    ) -> None:
        """
        Validate that a synthetic value is compatible with a
        documented string field.
        """

        if expected_type is None:
            raise ValueError(
                "Generated test case contains a synthetic concrete "
                f"value for request field '{field_name}', but its "
                "documented type could not be determined."
            )

        if expected_type != "string":
            raise ValueError(
                "Generated test case contains a synthetic string "
                f"value for request field '{field_name}', but the "
                f"documented type is '{expected_type}'."
            )

    def _validate_boolean_type(
        self,
        field_name: str,
        expected_type: str | None,
    ) -> None:
        """
        Validate that a synthetic value is compatible with a
        documented boolean field.
        """

        if expected_type is None:
            raise ValueError(
                "Generated test case contains a synthetic concrete "
                f"value for request field '{field_name}', but its "
                "documented type could not be determined."
            )

        if expected_type != "boolean":
            raise ValueError(
                "Generated test case contains a synthetic boolean "
                f"value for request field '{field_name}', but the "
                f"documented type is '{expected_type}'."
            )

    def _validate_numeric_type(
        self,
        field_name: str,
        field_value: float,
        expected_type: str | None,
    ) -> None:
        """
        Validate that a synthetic numeric value is compatible with
        a documented number/integer field.
        """

        if expected_type is None:
            raise ValueError(
                "Generated test case contains a synthetic concrete "
                f"value for request field '{field_name}', but its "
                "documented type could not be determined."
            )

        if expected_type == "integer":

            if isinstance(field_value, float) and not field_value.is_integer():
                raise ValueError(
                    "Generated test case contains a synthetic "
                    "non-integer value for integer request field "
                    f"'{field_name}': {field_value}."
                )

            return

        if expected_type != "number":
            raise ValueError(
                "Generated test case contains a synthetic numeric "
                f"value for request field '{field_name}', but the "
                f"documented type is '{expected_type}'."
            )

    # ------------------------------------------------------------------
    # CONCRETE VALUES
    # ------------------------------------------------------------------

    def _validate_concrete_value(
        self,
        field_name: str,
        field_value: Any,
        context: str,
    ) -> None:
        """
        Concrete values must be explicitly grounded in API context.
        """

        normalized_context = context.lower()
        normalized_value = str(field_value).lower()

        if normalized_value not in normalized_context:
            raise ValueError(
                "Generated test case contains an undocumented "
                f"concrete value for request field "
                f"'{field_name}': {field_value}."
            )

    # ------------------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------------------

    @staticmethod
    def _category_flags(
        category: str,
    ) -> dict[str, bool]:
        """
        Classify a generated test case category.
        """

        normalized = category.lower()

        return {
            "validation": ("validation" in normalized or "negative" in normalized),
            "auth": ("auth" in normalized or "authorization" in normalized),
            "errors": ("error" in normalized),
        }

    @staticmethod
    def _is_validation_category(
        category: str,
    ) -> bool:
        """
        Identify negative / validation test categories.

        Kept for backwards compatibility with existing callers/tests.
        """

        normalized = category.lower()

        return "validation" in normalized or "negative" in normalized

    # ------------------------------------------------------------------
    # PLACEHOLDER
    # ------------------------------------------------------------------

    @classmethod
    def _is_placeholder(
        cls,
        value: str,
    ) -> bool:
        """
        Return True for generated placeholders such as:

            <NAME>
            <PRICE>
            <PRODUCT_ID>
            <TOKEN>
        """

        return bool(
            cls._PLACEHOLDER_PATTERN.fullmatch(
                value.strip(),
            )
        )
