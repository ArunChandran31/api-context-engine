from dataclasses import dataclass

from app.ai.deterministic_provider import DeterministicLLMProvider
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.provider import LLMProvider
from app.ai.question_answering_service import QuestionAnsweringService
from app.core.config import Settings, get_settings
from app.rag.dependencies import RAGDependencies, build_rag_dependencies


@dataclass(frozen=True)
class AIDependencies:
    """
    Application-level dependencies for AI question answering.
    """

    llm_provider: LLMProvider
    prompt_builder: GroundedPromptBuilder
    question_answering_service: QuestionAnsweringService


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

    llm_provider = DeterministicLLMProvider(
        response=(
            "The deterministic AI provider is configured correctly. "
            "A production LLM provider has not been configured yet."
        ),
    )

    prompt_builder = GroundedPromptBuilder()

    question_answering_service = QuestionAnsweringService(
        retrieval_service=rag.retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        retrieval_limit=application_settings.rag_retrieval_limit,
    )

    return AIDependencies(
        llm_provider=llm_provider,
        prompt_builder=prompt_builder,
        question_answering_service=question_answering_service,
    )
