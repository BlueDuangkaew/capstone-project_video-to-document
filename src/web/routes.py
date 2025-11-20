from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Welcome to the Video-to-Documentation Platform"}

@router.get("/health")
def health():
    return {"status": "ok"}
