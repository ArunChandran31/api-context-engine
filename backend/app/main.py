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

# Import models so SQLAlchemy registers them
from app.database.models.api_specification import ApiSpecification  # noqa: F401
from app.database.models.endpoint import Endpoint  # noqa: F401
from app.database.session import engine


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


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
