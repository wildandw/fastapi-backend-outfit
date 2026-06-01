import os
import uuid
import time
import base64
import requests

from datetime import datetime
from fastapi import HTTPException

from services.image_service import ImageService
from services.wardrobe_service import WardrobeService

from utils.firebase import get_db_reference


GPU_SERVER_URL = os.getenv("GPU_SERVER_URL")


class TryOnService:

    def __init__(self):

        self.image_service = ImageService()
        self.wardrobe_service = WardrobeService()

    # =====================================================
    # DOWNLOAD IMAGE
    # =====================================================
    def _download_image(self, url: str) -> bytes:

        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Gagal mengunduh gambar: {url}"
            )

        return response.content

    # =====================================================
    # BASE64
    # =====================================================
    def _encode_to_base64(self, image_bytes: bytes) -> str:

        return base64.b64encode(
            image_bytes
        ).decode("utf-8")

    def _decode_from_base64(self, b64_string: str) -> bytes:

        return base64.b64decode(b64_string)

    # =====================================================
    # INFERENCE
    # =====================================================
    def _run_inference(
        self,
        person_b64: str,
        cloth_b64: str,
        category: str
    ) -> str:

        payload = {
            "person_b64": person_b64,
            "cloth_b64": cloth_b64,
            "category": category
        }

        try:

            response = requests.post(
                f"{GPU_SERVER_URL}/tryon",
                json=payload,
                timeout=600
            )

            if response.status_code != 200:

                raise HTTPException(
                    status_code=500,
                    detail=f"Inferensi {category} gagal"
                )

            return response.json()["result_b64"]

        except requests.RequestException as e:

            raise HTTPException(
                status_code=500,
                detail=f"Gagal koneksi GPU server: {str(e)}"
            )

    # =====================================================
    # PROCESS TRYON
    # =====================================================
    def process_tryon(
        self,
        user_id: str,
        person_image_bytes: bytes,
        top_item_id: str,
        bottom_item_id: str
    ) -> dict:

        start_time = time.time()

        # =====================================================
        # GET ITEM
        # =====================================================

        top_item = self.wardrobe_service.get_item_by_id(
            user_id,
            top_item_id
        )

        bottom_item = self.wardrobe_service.get_item_by_id(
            user_id,
            bottom_item_id
        )

        if not top_item or not bottom_item:

            raise HTTPException(
                status_code=404,
                detail="Item pakaian tidak ditemukan"
            )

        # =====================================================
        # DOWNLOAD CLOTHES IMAGE
        # =====================================================

        person_bytes = person_image_bytes

        top_bytes = self._download_image(
            top_item["imageUrl"]
        )

        bottom_bytes = self._download_image(
            bottom_item["imageUrl"]
        )

        # =====================================================
        # RESIZE
        # =====================================================

        person_bytes = self.image_service.resize_image(
            person_bytes
        )

        top_bytes = self.image_service.resize_image(
            top_bytes
        )

        bottom_bytes = self.image_service.resize_image(
            bottom_bytes
        )

        # =====================================================
        # BASE64
        # =====================================================

        person_b64 = self._encode_to_base64(
            person_bytes
        )

        top_b64 = self._encode_to_base64(
            top_bytes
        )

        bottom_b64 = self._encode_to_base64(
            bottom_bytes
        )

        # =====================================================
        # STAGE 1 - TOPS
        # =====================================================

        top_result_b64 = self._run_inference(
            person_b64,
            top_b64,
            "tops"
        )

        # =====================================================
        # STAGE 2 - BOTTOMS
        # =====================================================

        intermediate_bytes = self._decode_from_base64(
            top_result_b64
        )

        intermediate_b64 = self._encode_to_base64(
            intermediate_bytes
        )

        final_result_b64 = self._run_inference(
            intermediate_b64,
            bottom_b64,
            "bottoms"
        )

        final_bytes = self._decode_from_base64(
            final_result_b64
        )

        # =====================================================
        # UPLOAD RESULT
        # =====================================================

        tryon_id = str(uuid.uuid4())

        result_image_url = self.image_service.upload_to_cloudinary(
            final_bytes,
            folder=f"tryon/{user_id}",
            public_id=tryon_id
        )

        # =====================================================
        # SAVE FIREBASE
        # =====================================================

        processing_time = round(
            time.time() - start_time,
            2
        )

        tryon_data = {

            "tryon_id": tryon_id,

            "result_image_url": result_image_url,

            "top_item_id": top_item_id,

            "bottom_item_id": bottom_item_id,

            "processing_time_seconds": processing_time,

            "created_at": datetime.utcnow().isoformat()
        }

        ref = get_db_reference(
            f"users/{user_id}/tryon/{tryon_id}"
        )

        ref.set(tryon_data)

        return tryon_data

    # =====================================================
    # HISTORY
    # =====================================================
    def get_history(self, user_id: str) -> list:

        ref = get_db_reference(
            f"users/{user_id}/tryon"
        )

        data = ref.get()

        if not data:
            return []

        return list(data.values())

    # =====================================================
    # DELETE RESULT
    # =====================================================
    def delete_result(
        self,
        user_id: str,
        tryon_id: str
    ) -> bool:

        ref = get_db_reference(
            f"users/{user_id}/tryon/{tryon_id}"
        )

        existing = ref.get()

        if not existing:
            return False

        ref.delete()

        return True