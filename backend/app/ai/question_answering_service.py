import logging
from dataclasses import dataclass
from typing import Any

from app.ai.models import GenerationResult
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.provider import LLMProvider
from app.cache.keys import build_ai_question_cache_key
from app.cache.service import CacheService
from app.core.config import get_settings
from app.rag.retrieval_service import RAGRetrievalService, RetrievalResult
from app.utils.timing import Timer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QuestionAnswerResult:
    """
    AI answer together with the API context used to generate it.
    """

    answer: GenerationResult
    sources: list[RetrievalResult]


class QuestionAnsweringService:
    """
    Orchestrates retrieval-grounded API question answering.

    Retrieves relevant indexed API context, builds a grounded
    generation request, delegates text generation to the configured
    LLM provider, and preserves the retrieved context for source
    attribution.

    AI question results are cached in Redis so repeated questions
    can
    bypass both retrieval and LLM generation.
    """

    def __init__(
        self,
        retrieval_service: RAGRetrievalService,
        prompt_builder: GroundedPromptBuilder,
        llm_provider: LLMProvider,
        cache_service: CacheService,
        retrieval_limit: int = 5,
    ) -> None:
        if retrieval_limit <= 0:
            raise ValueError("Retrieval limit must be positive.")

        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._llm_provider = llm_provider
        self._cache_service = cache_service
        self._retrieval_limit = retrieval_limit

    def answer(
        self,
        question: str,
        specification_id: int,
    ) -> QuestionAnswerResult:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if specification_id <= 0:
            raise ValueError("Specification ID must be greater than zero.")

        settings = get_settings()

        provider = settings.llm_provider
        model = self._get_provider_model(provider, settings)

        cache_key = build_ai_question_cache_key(
            question=question,
            specification_id=specification_id,
            provider=provider,
            model=model,
        )

        total_timer = Timer()
        total_timer.start()

        cache_timer = Timer()
        cache_timer.start()

        cached_value = self._cache_service.get(cache_key)

        cache_get_ms = cache_timer.stop()

        if cached_value is not None:
            cached_result = self._deserialize_cached_result(cached_value)

            if cached_result is not None:
                total_ms = total_timer.stop()

                logger.info(
                    "AI question cache HIT",
                    extra={
                        "cache_hit": True,
                        "cache_get_ms": round(cache_get_ms, 2),
                        "total_ms": round(total_ms, 2),
                        "context_count": len(cached_result.sources),
                    },
                )

                return cached_result

        logger.info(
            "AI question cache MISS",
            extra={
                "cache_hit": False,
                "cache_get_ms": round(cache_get_ms, 2),
                "cache_key": cache_key,
            },
        )

        retrieval_timer = Timer()
        retrieval_timer.start()

        contexts = self._retrieval_service.retrieve(
            query=question,
            limit=self._retrieval_limit,
            specification_id=specification_id,
        )

        retrieval_ms = retrieval_timer.stop()

        prompt_timer = Timer()
        prompt_timer.start()

        request = self._prompt_builder.build(
            question=question,
            contexts=contexts,
        )

        prompt_ms = prompt_timer.stop()

        generation_timer = Timer()
        generation_timer.start()

        generation_result = self._llm_provider.generate(request)

        generation_ms = generation_timer.stop()

        result = QuestionAnswerResult(
            answer=generation_result,
            sources=contexts,
        )

        cache_set_timer = Timer()
        cache_set_timer.start()

        self._cache_service.set(
            cache_key,
            self._serialize_result(result),
            ttl_seconds=settings.redis_cache_ttl_seconds,
        )

        cache_set_ms = cache_set_timer.stop()

        total_ms = total_timer.stop()

        retrieval_timing = getattr(
            self._retrieval_service,
            "last_timing",
            {
                "embedding_ms": 0.0,
                "search_ms": 0.0,
                "reconstruction_ms": 0.0,
            },
        )

        logger.info(
            "AI question completed",
            extra={
                "cache_hit": False,
                "cache_get_ms": round(cache_get_ms, 2),
                "retrieval_ms": round(retrieval_ms, 2),
                "embedding_ms": retrieval_timing["embedding_ms"],
                "search_ms": retrieval_timing["search_ms"],
                "reconstruction_ms": retrieval_timing["reconstruction_ms"],
                "cache_set_ms": round(cache_set_ms, 2),
                "total_ms": round(total_ms, 2),
                "prompt_ms": round(prompt_ms, 2),
                "generation_ms": round(generation_ms, 2),
                "context_count": len(contexts),
            },
        )

        return result

    @staticmethod
    def _get_provider_model(
        provider: str,
        settings: Any,
    ) -> str:
        """
        Return the configured model for the active LLM provider.
        """

        if provider == "groq":
            return settings.groq_model

        if provider == "gemini":
            return settings.gemini_model

        return "deterministic"

    @staticmethod
    def _serialize_result(
        result: QuestionAnswerResult,
    ) -> dict[str, Any]:
        """
        Convert an AI question result into a JSON-serializable value.
        """

        return {
            "answer": {
                "content": result.answer.content,
            },
            "sources": [
                {
                    "content": source.content,
                    "score": source.score,
                    "metadata": source.metadata,
                }
                for source in result.sources
            ],
        }

    @staticmethod
    def _deserialize_cached_result(
        value: Any,
    ) -> QuestionAnswerResult | None:
        """
        Reconstruct an AI question result from a cached value.

        Invalid or incomplete cache entries are ignored so a bad cache
        value never breaks the normal AI question flow.
        """

        if not isinstance(value, dict):
            return None

        answer_value = value.get("answer")
        sources_value = value.get("sources")

        if not isinstance(answer_value, dict):
            return None

        if not isinstance(answer_value.get("content"), str):
            return None

        if not isinstance(sources_value, list):
            return None

        sources: list[RetrievalResult] = []

        for source in sources_value:
            if not isinstance(source, dict):
                return None

            content = source.get("content")
            score = source.get("score")
            metadata = source.get("metadata")

            if not isinstance(content, str):
                return None

            if not isinstance(score, (int, float)):
                return None

            if not isinstance(metadata, dict):
                return None

            sources.append(
                RetrievalResult(
                    content=content,
                    score=float(score),
                    metadata=metadata,
                )
            )

        return QuestionAnswerResult(
            answer=GenerationResult(
                content=answer_value["content"],
            ),
            sources=sources,
        )
