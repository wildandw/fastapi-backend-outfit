from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
import uuid
from datetime import datetime
from PIL import Image
import io

from middleware.auth import get_current_user
from models.schemas import (
    ClothingItemCreate,
    ClothingItemUpdate,
    ClothingItemResponse,
    DetectedAttributes
)

from services.removebg_service import RemoveBackgroundService
from services.wardrobe_service import WardrobeService
from services.attribute_detection_service import AttributeDetectionService
from services.image_service import ImageService

router = APIRouter()

removebg_service = RemoveBackgroundService()
wardrobe_service = WardrobeService()
detection_service = AttributeDetectionService()
image_service = ImageService()


# =====================================================
# UPLOAD IMAGE
# =====================================================
@router.post("/upload", response_model=dict)
async def upload_clothing_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):

    try:

        # =====================================================
        # VALIDASI FILE
        # =====================================================
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"File harus berupa gambar. Diterima: {file.content_type}"
            )

        # =====================================================
        # BACA FILE
        # =====================================================
        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="File gambar kosong"
            )

        # =====================================================
        # VALIDASI IMAGE DENGAN PIL
        # =====================================================
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="File gambar rusak atau format tidak didukung"
            )

        # =====================================================
        # REMOVE BACKGROUND
        # =====================================================
        removed_bg_bytes = removebg_service.remove_background(
            image_bytes
        )

        # =====================================================
        # CREATE THUMBNAIL
        # =====================================================
        thumbnail_bytes = image_service.create_thumbnail(
            removed_bg_bytes
        )

        # =====================================================
        # UPLOAD CLOUDINARY
        # =====================================================
        image_url = image_service.upload_to_cloudinary(
            thumbnail_bytes,
            folder=f"wardrobe/{current_user['uid']}"
        )

        # =====================================================
        # DETECT ATTRIBUTES
        # =====================================================
        detected_attrs = detection_service.detect_attributes(
            thumbnail_bytes
        )

        return {
            "image_url": image_url,
            "detected_attributes": detected_attrs,
            "message": "Gambar berhasil diunggah"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload gagal: {str(e)}"
        )


# =====================================================
# ADD ITEM
# =====================================================
@router.post("/items", response_model=ClothingItemResponse)
async def add_clothing_item(
    item_data: ClothingItemCreate,
    image_url: str,
    current_user: dict = Depends(get_current_user)
):

    item_id = str(uuid.uuid4())

    item = {
        "id": item_id,
        "name": item_data.name,
        "category": item_data.category,
        "color": item_data.color,
        "style": item_data.style,
        "activities": item_data.activities,
        "pattern": item_data.pattern,
        "imageUrl": image_url,
        "createdAt": datetime.utcnow().isoformat()
    }

    saved_item = wardrobe_service.save_item(
        current_user["uid"],
        item_id,
        item
    )

    return saved_item


# =====================================================
# GET ALL ITEMS
# =====================================================
@router.get("/items", response_model=List[ClothingItemResponse])
async def get_wardrobe_items(
    current_user: dict = Depends(get_current_user)
):

    items = wardrobe_service.get_all_items(
        current_user["uid"]
    )

    return items


# =====================================================
# GET SINGLE ITEM
# =====================================================
@router.get("/items/{item_id}", response_model=ClothingItemResponse)
async def get_clothing_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):

    item = wardrobe_service.get_item_by_id(
        current_user["uid"],
        item_id
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item pakaian tidak ditemukan"
        )

    return item


# =====================================================
# UPDATE ITEM
# =====================================================
@router.put("/items/{item_id}", response_model=ClothingItemResponse)
async def update_clothing_item(
    item_id: str,
    item_data: ClothingItemUpdate,
    current_user: dict = Depends(get_current_user)
):

    updated_item = wardrobe_service.update_item(
        current_user["uid"],
        item_id,
        item_data.dict(exclude_none=True)
    )

    if not updated_item:
        raise HTTPException(
            status_code=404,
            detail="Item pakaian tidak ditemukan"
        )

    return updated_item


# =====================================================
# DELETE ITEM
# =====================================================
@router.delete("/items/{item_id}")
async def delete_clothing_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):

    success = wardrobe_service.delete_item(
        current_user["uid"],
        item_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Item pakaian tidak ditemukan"
        )

    return {
        "message": "Item pakaian berhasil dihapus"
    }


# =====================================================
# DETECT ATTRIBUTES
# =====================================================
@router.post(
    "/detect-attributes",
    response_model=DetectedAttributes
)
async def detect_attributes(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):

    image_bytes = await file.read()

    detected = detection_service.detect_attributes(
        image_bytes
    )

    return detected