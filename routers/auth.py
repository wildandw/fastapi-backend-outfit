from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from middleware.auth import get_current_user
from utils.firebase import auth

router = APIRouter()


@router.get("/auth/verify")
def verify_user(
    current_user: dict = Depends(get_current_user)
):
    print("VERIFY USER")
    print(current_user)

    return {
        "message": "Token valid",
        "uid": current_user["uid"]
    }


# =====================================================
# FORGOT PASSWORD
# =====================================================

class CheckEmailRequest(BaseModel):
    email: str


@router.post("/auth/check-email")
def check_email(request: CheckEmailRequest):

    try:

        user = auth.get_user_by_email(
            request.email
        )

        print("EMAIL TERDAFTAR")
        print("UID:", user.uid)
        print("EMAIL:", user.email)

        return {
            "exists": True,
            "message": "Email terdaftar"
        }

    except auth.UserNotFoundError:

        print("EMAIL TIDAK TERDAFTAR")

        raise HTTPException(
            status_code=404,
            detail="Email tidak terdaftar"
        )

    except Exception as e:

        print("CHECK EMAIL ERROR:")
        print(type(e))
        print(str(e))

        raise HTTPException(
            status_code=500,
            detail="Gagal memeriksa email"
        )