from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
import uuid
from datetime import datetime

from middleware.auth import get_current_user
from models.schemas import (
    ClothingItemCreate, ClothingItemUpdate,
    ClothingItemResponse, DetectedAttributes
)
from services.wardrobe_service import WardrobeService
from services.attribute_detection_service import AttributeDetectionService
from services.image_service import ImageService

router = APIRouter()
wardrobe_service = WardrobeService()
detection_service = AttributeDetectionService()
image_service = ImageService()


@router.post("/upload", response_model=dict)
async def upload_clothing_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    SKPL-F-004: Menerima file gambar dari galeri perangkat pengguna
    SKPL-F-005: Menghapus latar belakang menggunakan rembg.remove()
    SKPL-F-006: Mengunggah gambar ke Cloudinary
    SKPL-F-007: Mendeteksi atribut pakaian secara otomatis
    """
    # Validasi format file
    if file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
        raise HTTPException(
            status_code=400,
            detail="Format file tidak valid. Gunakan JPG atau PNG"
        )

    # Membaca konten file menggunakan await file.read()
    image_bytes = await file.read()

    # SKPL-F-005: Menghapus latar belakang menggunakan rembg.remove()
    removed_bg_bytes = image_service.remove_background(image_bytes)

    # Membuat thumbnail menggunakan image.thumbnail((512, 512))
    thumbnail_bytes = image_service.create_thumbnail(removed_bg_bytes)

    # SKPL-F-006: Mengunggah gambar ke Cloudinary
    image_url = image_service.upload_to_cloudinary(
        thumbnail_bytes,
        folder=f"wardrobe/{current_user['uid']}"
    )

    # SKPL-F-007: Mendeteksi atribut pakaian secara otomatis
    detected_attrs = detection_service.detect_attributes(thumbnail_bytes)

    return {
        "image_url": image_url,
        "detected_attributes": detected_attrs,
        "message": "Gambar berhasil diunggah dan atribut terdeteksi"
    }


# ── SKPL-F-004, F-006, F-007 (simpan metadata) ──
@router.post("/items", response_model=ClothingItemResponse)
async def add_clothing_item(
    item_data: ClothingItemCreate,
    image_url: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Menyimpan metadata pakaian ke Firebase Realtime Database
    menggunakan db.reference('wardrobe/{uid}').push(metadata)
    """
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

    saved_item = wardrobe_service.save_item(current_user["uid"], item_id, item)
    return saved_item


# ── SKPL-F-008 ──
@router.get("/items", response_model=List[ClothingItemResponse])
async def get_wardrobe_items(
    current_user: dict = Depends(get_current_user)
):
    """
    SKPL-F-008: Mengambil seluruh koleksi pakaian pengguna
    dari Firebase Realtime Database menggunakan
    db.reference('wardrobe/{uid}').get()
    """
    items = wardrobe_service.get_all_items(current_user["uid"])
    return items


# ── SKPL-F-008 (per item) ──
@router.get("/items/{item_id}", response_model=ClothingItemResponse)
async def get_clothing_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Mengambil satu item pakaian berdasarkan item_id
    dari Firebase Realtime Database
    """
    item = wardrobe_service.get_item_by_id(current_user["uid"], item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item pakaian tidak ditemukan")
    return item


# ── SKPL-F-009 ──
@router.put("/items/{item_id}", response_model=ClothingItemResponse)
async def update_clothing_item(
    item_id: str,
    item_data: ClothingItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    SKPL-F-009: Mengubah metadata pakaian yang telah disimpan
    menggunakan db.reference('wardrobe/{uid}/{item_id}').update()
    """
    updated_item = wardrobe_service.update_item(
        current_user["uid"], item_id,
        item_data.dict(exclude_none=True)
    )
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item pakaian tidak ditemukan")
    return updated_item


# ── SKPL-F-010 ──
@router.delete("/items/{item_id}")
async def delete_clothing_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    SKPL-F-010: Menghapus data pakaian dari lemari digital
    menggunakan db.reference('wardrobe/{uid}/{item_id}').delete()
    """
    success = wardrobe_service.delete_item(current_user["uid"], item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item pakaian tidak ditemukan")
    return {"message": "Item pakaian berhasil dihapus"}


# ── SKPL-F-007 (deteksi ulang manual) ──
@router.post("/detect-attributes", response_model=DetectedAttributes)
async def detect_attributes(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    SKPL-F-007: Mendeteksi atribut pakaian secara otomatis
    menggunakan colorthief untuk warna dan CLIP model untuk kategori
    Hasil dapat diedit oleh pengguna setelah deteksi
    """
    image_bytes = await file.read()
    detected = detection_service.detect_attributes(image_bytes)
    return detected
