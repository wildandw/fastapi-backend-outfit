from fastapi import APIRouter, Depends
from middleware.auth import get_current_user

router = APIRouter()

@router.get("/auth/verify")
def verify_user(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "Token valid",
        "uid": current_user["uid"]
    }