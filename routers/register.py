from fastapi import APIRouter, Depends
from middleware.auth import get_current_user
from utils.firebase import get_db_reference
from models.schemas import UserProfileRequest

router = APIRouter()

@router.post("/users/profile")
def save_user_profile(
    data: UserProfileRequest,
    current_user: dict = Depends(get_current_user)
):

    uid = current_user["uid"]

    user_data = {
        "username": data.username,
        "email": data.email
    }

    ref = get_db_reference(f"users/{uid}")
    ref.set(user_data)

    return {
        "message": "Profile berhasil disimpan"
    }