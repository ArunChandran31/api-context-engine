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
from app.ai.groq_provider import GroqLLMProvider
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
from app.core.config import Settings, get_settings
from app.rag.dependencies import (
    RAGDependencies,
    build_rag_dependencies,
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


def build_ai_dependencies(
    settings: Settings | None = None,
    rag_dependencies: RAGDependencies | None = None,
) -> AIDependencies:
    """
    Build the application's AI dependency graph.

    Dependencies may be supplied explicitly to support tests and
    alternate runtime configurations.
    """

    application_settings = settings or get_settings()

    rag = rag_dependencies or build_rag_dependencies(
        settings=application_settings,
    )

    if application_settings.llm_provider == "deterministic":
        llm_provider: LLMProvider = DeterministicLLMProvider(
            response=(
                "The deterministic AI provider is configured correctly. "
                "A production LLM provider has not been configured yet."
            ),
        )

    elif application_settings.llm_provider == "groq":
        if not application_settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER is 'groq'.")

        llm_provider = GroqLLMProvider(
            api_key=application_settings.groq_api_key,
            model=application_settings.groq_model,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {application_settings.llm_provider}"
        )

    prompt_builder = GroundedPromptBuilder()

    question_answering_service = QuestionAnsweringService(
        retrieval_service=rag.retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        retrieval_limit=application_settings.rag_retrieval_limit,
    )

    test_case_prompt_builder = TestCasePromptBuilder()

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

    test_case_generation_service = TestCaseGenerationService(
        retrieval_service=rag.retrieval_service,
        prompt_builder=test_case_prompt_builder,
        generator=test_case_generator,
        retrieval_limit=application_settings.rag_retrieval_limit,
    )

    debug_prompt_builder = DebugPromptBuilder()

    debug_generator = DeterministicDebugGenerator(
        explanation=("The deterministic debug generator is configured correctly."),
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
