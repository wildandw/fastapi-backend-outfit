from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form
)

from middleware.auth import get_current_user
from services.tryon_service import TryOnService

router = APIRouter()

tryon_service = TryOnService()


@router.post("/")
async def virtual_try_on(
    person_image: UploadFile = File(...),
    top_item_id: str = Form(...),
    bottom_item_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):

    person_bytes = await person_image.read()

    result = tryon_service.process_tryon(
        user_id=current_user["uid"],
        person_image_bytes=person_bytes,
        top_item_id=top_item_id,
        bottom_item_id=bottom_item_id
    )

    return result


@router.get("/history")
async def get_tryon_history(
    current_user: dict = Depends(get_current_user)
):
    history = tryon_service.get_history(
        current_user["uid"]
    )

    return {
        "history": history
    }


@router.delete("/{tryon_id}")
async def delete_tryon_result(
    tryon_id: str,
    current_user: dict = Depends(get_current_user)
):

    success = tryon_service.delete_result(
        current_user["uid"],
        tryon_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Hasil virtual try-on tidak ditemukan"
        )

    return {
        "message": "Hasil virtual try-on berhasil dihapus"
    }