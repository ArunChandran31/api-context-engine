from dataclasses import dataclass

from app.ai.debug_generator import DebugGenerator
from app.ai.debug_prompt_builder import DebugPromptBuilder
from app.ai.debug_service import DebugService
from app.ai.deterministic_debug_generator import (
    DeterministicDebugGenerator,
)
from app.ai.deterministic_provider import DeterministicLLMProvider
from app.ai.deterministic_test_case_generator import (
    DeterministicTestCaseGenerator,
)
from app.ai.fallback_provider import FallbackLLMProvider
from app.ai.gemini_provider import GeminiLLMProvider
from app.ai.groq_provider import GroqLLMProvider
from app.ai.llm_debug_generator import LLMDebugGenerator
from app.ai.llm_test_case_generator import LLMTestCaseGenerator
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.provider import LLMProvider
from app.ai.question_answering_service import (
    QuestionAnsweringService,
)
from app.ai.test_case_generation_service import (
    TestCaseGenerationService,
)
from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationResult,
)
from app.ai.test_case_prompt_builder import (
    TestCasePromptBuilder,
)
from app.ai.test_case_validator import TestCaseGroundingValidator
from app.core.config import Settings
from app.core.runtime_settings import get_effective_settings
from app.rag.dependencies import (
    RAGDependencies,
    build_rag_dependencies,
    get_rag_dependencies,
)


@dataclass(frozen=True)
class AIDependencies:
    """
    Application-level AI dependency graph.
    """

    llm_provider: LLMProvider

    prompt_builder: GroundedPromptBuilder
    question_answering_service: QuestionAnsweringService

    test_case_prompt_builder: TestCasePromptBuilder
    test_case_generation_service: TestCaseGenerationService

    debug_prompt_builder: DebugPromptBuilder
    debug_generator: DebugGenerator
    debug_service: DebugService


def _build_single_llm_provider(
    settings: Settings,
    provider_name: str,
    *,
    max_retries: int | None = None,
) -> LLMProvider:
    """
    Build one concrete LLM provider from application settings.

    max_retries can be overridden by the caller so that the fallback
    layer can take responsibility for cross-provider failover without
    waiting for the primary provider's internal retry loop.
    """

    if provider_name == "deterministic":
        return DeterministicLLMProvider(
            response=(
                "The deterministic AI provider is configured correctly. "
                "A production LLM provider has not been configured yet."
            ),
        )

    if provider_name == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM provider is 'groq'.")

        effective_max_retries = (
            settings.llm_max_retries if max_retries is None else max_retries
        )

        return GroqLLMProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=effective_max_retries,
            retry_backoff_seconds=settings.llm_retry_backoff_seconds,
        )

    if provider_name == "gemini":
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM provider is 'gemini'."
            )

        return GeminiLLMProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    raise ValueError(f"Unsupported LLM provider: {provider_name}")


def _build_llm_provider(
    settings: Settings,
) -> LLMProvider:
    """
    Build the application's effective LLM provider.

    When fallback is enabled, the configured primary provider is wrapped
    with the configured fallback provider.

    The primary Groq provider uses zero internal retries when it is
    wrapped by the fallback provider. This allows a transient Groq
    failure such as HTTP 429 to be handed to the fallback provider
    immediately instead of waiting through Groq's retry/backoff cycle.
    """

    fallback_enabled = (
        settings.llm_fallback_enabled
        and settings.llm_provider != settings.llm_fallback_provider
        and settings.llm_provider != "deterministic"
    )

    primary_max_retries: int | None = None

    if fallback_enabled and settings.llm_provider == "groq":
        primary_max_retries = 0

    primary_provider = _build_single_llm_provider(
        settings,
        settings.llm_provider,
        max_retries=primary_max_retries,
    )

    if not fallback_enabled:
        return primary_provider

    fallback_provider = _build_single_llm_provider(
        settings,
        settings.llm_fallback_provider,
    )

    return FallbackLLMProvider(
        primary_provider=primary_provider,
        fallback_provider=fallback_provider,
        fallback_enabled=True,
    )


def build_ai_dependencies(
    settings: Settings | None = None,
    rag_dependencies: RAGDependencies | None = None,
) -> AIDependencies:
    """
    Build the application's AI dependency graph.

    Dependencies may be supplied explicitly to support tests and
    alternate runtime configurations.
    """

    application_settings = settings or get_effective_settings()

    if rag_dependencies is not None:
        rag = rag_dependencies
    elif settings is None:
        rag = get_rag_dependencies()
    else:
        rag = build_rag_dependencies(
            settings=application_settings,
        )

    llm_provider = _build_llm_provider(
        application_settings,
    )

    prompt_builder = GroundedPromptBuilder()

    question_answering_service = QuestionAnsweringService(
        retrieval_service=rag.retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        retrieval_limit=application_settings.rag_retrieval_limit,
    )

    test_case_prompt_builder = TestCasePromptBuilder()

    if application_settings.llm_provider == "deterministic":
        test_case_generator: TestCaseGenerator = DeterministicTestCaseGenerator(
            result=TestCaseGenerationResult(
                test_cases=[
                    GeneratedTestCase(
                        category="Positive",
                        description=(
                            "The deterministic test case generator "
                            "is configured correctly."
                        ),
                    )
                ]
            )
        )
    else:
        test_case_generator = LLMTestCaseGenerator(
            llm_provider=llm_provider,
        )

    test_case_validator = TestCaseGroundingValidator()

    test_case_generation_service = TestCaseGenerationService(
        retrieval_service=rag.retrieval_service,
        prompt_builder=test_case_prompt_builder,
        generator=test_case_generator,
        validator=test_case_validator,
        retrieval_limit=application_settings.rag_retrieval_limit,
    )

    debug_prompt_builder = DebugPromptBuilder()

    if application_settings.llm_provider == "deterministic":
        debug_generator: DebugGenerator = DeterministicDebugGenerator(
            explanation=(
                "The deterministic debug generator is " "configured correctly."
            ),
        )
    else:
        debug_generator = LLMDebugGenerator(
            llm_provider=llm_provider,
        )

    debug_service = DebugService(
        retrieval_service=rag.retrieval_service,
        prompt_builder=debug_prompt_builder,
        debug_generator=debug_generator,
        retrieval_limit=application_settings.rag_retrieval_limit,
    )

    return AIDependencies(
        llm_provider=llm_provider,
        prompt_builder=prompt_builder,
        question_answering_service=question_answering_service,
        test_case_prompt_builder=test_case_prompt_builder,
        test_case_generation_service=test_case_generation_service,
        debug_prompt_builder=debug_prompt_builder,
        debug_generator=debug_generator,
        debug_service=debug_service,
    )
