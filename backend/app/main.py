from fastapi import FastAPI
from app.api.health import router as health_router

app = FastAPI(
    title="API Context Engine",
    description="A simple API context engine",
    version="0.1.0"
)
app.include_router(health_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the API Context Engine!"}
