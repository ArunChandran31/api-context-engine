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

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.database.base import Base
from app.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle events.
    Runs once when the application starts and once when it shuts down.
    """

    # Startup
    Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    # Future cleanup tasks will go here.
    # Example:
    # - Close Redis connections
    # - Stop background workers
    # - Release AI models


app = FastAPI(
    title="API Context Engine",
    description="An AI-powered platform for understanding, analysing, and interacting with API specifications.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(upload_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "API Context Engine",
        "version": "0.1.0",
        "status": "running",
    }
