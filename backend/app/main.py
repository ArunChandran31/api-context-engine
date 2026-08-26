import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai.exceptions import LLMProviderError
from app.api.ai import router as ai_router
from app.api.debug import router as debug_router
from app.api.endpoints import router as endpoint_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.api.specifications import router as specification_router
from app.api.test_cases import router as test_case_router
from app.api.upload import router as upload_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.database.base import Base

# Import models so SQLAlchemy registers them before create_all()
from app.database.models.api_specification import ApiSpecification  # noqa: F401
from app.database.models.endpoint import Endpoint  # noqa: F401
from app.database.session import engine

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """
    logger.info("Starting %s...", settings.app_name)

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

    # Preload the RAG embedding model during application startup.
    # This prevents the first AI request from paying the model-loading
    # cost (~80+ seconds in the current environment).
    try:
        from app.rag.dependencies import get_rag_dependencies

        rag_dependencies = get_rag_dependencies()

        logger.info("Loading RAG embedding model...")

        rag_dependencies.embedding_provider.warm_up()

        logger.info("RAG embedding model loaded successfully.")

    except Exception:
        logger.exception("Failed to preload RAG embedding model.")
        raise

    yield

    logger.info("Shutting down %s...", settings.app_name)


async def llm_provider_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Converts expected LLM provider failures into controlled API responses.
    """
    if not isinstance(exc, LLMProviderError):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "llm_provider_error",
            "message": str(exc),
        },
    )


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8443",
        "http://127.0.0.1:8443",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    LLMProviderError,
    llm_provider_exception_handler,
)

# Register API routers
app.include_router(health_router)

app.include_router(
    specification_router,
    prefix="/api",
)

app.include_router(
    endpoint_router,
    prefix="/api",
)

app.include_router(
    upload_router,
    prefix="/api",
)

app.include_router(
    ai_router,
    prefix="/api",
)

app.include_router(
    debug_router,
    prefix="/api",
)

app.include_router(
    test_case_router,
    prefix="/api",
)

app.include_router(
    rag_router,
    prefix="/api",
)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
