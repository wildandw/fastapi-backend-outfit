from utils.firebase import get_db_reference
from utils.cloudinary_helper import delete_image

from services.clothing_validator import ClothingValidator
from services.attribute_detection_service import AttributeDetectionService
from services.image_service import ImageService
from services.removebg_service import RemoveBackgroundService
from services.clip_service import CLIPService

from fastapi import HTTPException

import requests

class WardrobeService:

    def __init__(self):

        # =====================================================
        # SHARED CLIP MODEL
        # =====================================================

        self.clip_service = CLIPService()

        self.clothing_validator = ClothingValidator(
            self.clip_service
        )

        self.attribute_detection_service = (
            AttributeDetectionService(
                self.clip_service
            )
        )

        self.image_service = ImageService()

        self.removebg_service = (
            RemoveBackgroundService()
        )
        
    #====================================================
    # PROCESS UPLOAD
    # =====================================================
    def process_upload(
        self,
        image_bytes: bytes,
        user_id: str
    ) -> dict:

        # Remove Background

        removed_bg_bytes = (
            self.removebg_service.remove_background(
                image_bytes
            )
        )

        # Thumbnail

        thumbnail_bytes = (
            self.image_service.create_thumbnail(
                removed_bg_bytes
            )
        )

        # Upload Cloudinary

        upload_result = (
            self.image_service.upload_to_cloudinary(
                thumbnail_bytes,
                folder=f"wardrobe/{user_id}"
            )
        )

        image_url = upload_result["image_url"]

        public_id = upload_result["public_id"]

        # Detect Attributes

        detected_attributes = (
            self.attribute_detection_service
            .detect_attributes(
                thumbnail_bytes
            )
        )

        return {
            "image_url": image_url,
            "public_id": public_id,
            "detected_attributes": detected_attributes,
            "message": "Gambar berhasil diunggah"
        }   
    
    # =====================================================
    # validasi pakaian
    # =====================================================
    def validate_clothing(
        self,
        image_bytes: bytes,
        category: str
    ):

        is_valid = self.clothing_validator.validate(
            image_bytes=image_bytes,
            category=category
        )

        if not is_valid:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Gambar bukan pakaian kategori {category}"
                )
            )
            
    def download_image(
        self,
        image_url: str
    ) -> bytes:

        response = requests.get(
            image_url,
            timeout=30
        )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Gagal membaca gambar"
            )

        return response.content

    def save_item(self, user_id: str, item_id: str, item: dict) -> dict:
        """
        Menyimpan metadata pakaian ke Firebase Realtime Database
        menggunakan db.reference('users/{user_id}/wardrobe/{item_id}').set()
        """
        ref = get_db_reference(f"users/{user_id}/wardrobe/{item_id}")
        ref.set(item)
        return item

    def get_all_items(self, user_id: str) -> list:
        """
        Mengambil seluruh item pakaian pengguna
        menggunakan db.reference('users/{user_id}/wardrobe').get()
        """
        ref = get_db_reference(f"users/{user_id}/wardrobe")
        data = ref.get()
        if not data:
            return []
        return list(data.values())

    def get_item_by_id(self, user_id: str, item_id: str) -> dict:
        """
        Mengambil satu item pakaian berdasarkan item_id
        menggunakan db.reference('users/{user_id}/wardrobe/{item_id}').get()
        """
        ref = get_db_reference(f"users/{user_id}/wardrobe/{item_id}")
        return ref.get()

    def get_items_by_category(self, user_id: str, category: str) -> list:
        """
        Mengambil item pakaian berdasarkan kategori
        untuk digunakan sebagai kandidat rekomendasi
        """
        all_items = self.get_all_items(user_id)
        return [item for item in all_items if item.get("category") == category]

    def update_item(self, user_id: str, item_id: str, updates: dict) -> dict:
        """
        Mengubah metadata pakaian menggunakan
        db.reference('users/{user_id}/wardrobe/{item_id}').update()
        """
        ref = get_db_reference(f"users/{user_id}/wardrobe/{item_id}")
        existing = ref.get()
        if not existing:
            return None
        ref.update(updates)
        return {**existing, **updates}

    def delete_item(self, user_id: str, item_id: str) -> bool:

        ref = get_db_reference(
            f"users/{user_id}/wardrobe/{item_id}"
        )

        item = ref.get()

        if not item:
            return False

        public_id = item.get("publicId")

        if public_id:
            delete_image(public_id)

        ref.delete()

        return True
