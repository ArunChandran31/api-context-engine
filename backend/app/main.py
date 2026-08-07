# from fastapi import FastAPI
# from app.api.health import router as health_router
# from app.api.upload import router as upload_router
# from app.database.base import Base
# from app.database.session import engine

# app = FastAPI(
#     title="API Context Engine",
#     description="A simple API context engine",
#     version="0.1.0"
# )
# app.include_router(health_router)
# app.include_router(upload_router)

# @app.get("/")
# async def root():
#     return {"message": "Welcome to the API Context Engine!"}

# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

    yield

    logger.info("Shutting down %s...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
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
