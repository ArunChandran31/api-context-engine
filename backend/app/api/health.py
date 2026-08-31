import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.database.session import SessionLocal
from app.rag.dependencies import get_rag_dependencies

router = APIRouter(prefix="/health", tags=["Health"])

logger = logging.getLogger(__name__)


def _check_database() -> dict:
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database health check failed: %s", exc)
        return {
            "status": "error",
            "message": str(exc),
        }
    finally:
        db.close()


def _check_redis() -> dict:
    try:
        redis = get_redis_client()
        redis.ping()

        return {
            "status": "healthy",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis health check failed: %s", exc)
        return {
            "status": "degraded",
            "message": str(exc),
        }


def _check_vector_store() -> dict:
    try:
        dependencies = get_rag_dependencies()
        store = dependencies.vector_store

        return {
            "status": "healthy",
            "type": type(store).__name__,
            "records": len(store),
            "dimension": store.dimension,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Vector store health check failed: %s", exc)
        return {
            "status": "error",
            "message": str(exc),
        }


def _check_llm() -> dict:
    settings = get_settings()

    provider = settings.llm_provider

    if provider == "groq":
        configured = bool(settings.groq_api_key)
        model = settings.groq_model
    elif provider == "gemini":
        configured = bool(settings.gemini_api_key)
        model = settings.gemini_model
    elif provider == "deterministic":
        configured = True
        model = "deterministic"
    else:
        configured = False
        model = "unknown"

    return {
        "status": "configured" if configured else "error",
        "provider": provider,
        "model": model,
    }


@router.get("/")
async def health_check():
    database = _check_database()
    redis = _check_redis()
    vector_store = _check_vector_store()
    llm = _check_llm()

    service_statuses = [
        database["status"],
        redis["status"],
        vector_store["status"],
        llm["status"],
    ]

    if "error" in service_statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    settings = get_settings()

    return {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "services": {
            "database": database,
            "redis": redis,
            "vector_store": vector_store,
            "llm": llm,
        },
    }
