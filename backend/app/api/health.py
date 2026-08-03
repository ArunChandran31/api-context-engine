from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "API Context Engine", "version": "0.1.0"}
