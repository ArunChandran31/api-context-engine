from fastapi import APIRouter, File, UploadFile

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

@router.post("/")
async def upload_api(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }