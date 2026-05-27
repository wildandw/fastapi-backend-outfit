import requests
import base64
import uuid
import time
import os
from io import BytesIO
from PIL import Image
from datetime import datetime

from utils.firebase import get_db_reference
from utils.cloudinary_helper import upload_image
from services.wardrobe_service import WardrobeService
from fastapi import HTTPException

GPU_SERVER_URL = os.getenv("GPU_SERVER_URL")


class TryOnService:

    def __init__(self):
        self.wardrobe_service = WardrobeService()

    def _download_image(self, url: str) -> bytes:
        """
        Mengunduh gambar menggunakan requests.get(url).content
        dari URL Firebase atau Cloudinary
        """
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Gagal mengunduh gambar dari URL: {url}"
            )
        return response.content

    def _resize_image(self, image_bytes: bytes, max_size: int = 768) -> bytes:
        """
        Melakukan resize gambar ke maksimal 768px pada sisi terpanjang
        menggunakan image.thumbnail((768, 768)) sebelum
        dikirim ke FASHN-VTON Model
        """
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail((max_size, max_size))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def _encode_to_base64(self, image_bytes: bytes) -> str:
        """
        Mengkodekan bytes gambar ke Base64 string menggunakan
        base64.b64encode(buffer.getvalue()).decode('utf-8')
        untuk dikirim dalam payload JSON
        """
        return base64.b64encode(image_bytes).decode("utf-8")

    def _decode_from_base64(self, b64_string: str) -> bytes:
        """
        Mendekode Base64 string menggunakan base64.b64decode()
        menjadi bytes gambar hasil inferensi FASHN-VTON
        """
        return base64.b64decode(b64_string)

    def _run_inference(self, person_b64: str, cloth_b64: str, category: str) -> str:
        """
        Mengirimkan requests.post(GPU_URL, json=payload)
        ke endpoint FASHN-VTON untuk menjalankan inferensi
        dan mengembalikan result_b64 dari response JSON
        """
        payload = {
            "person_b64": person_b64,
            "cloth_b64": cloth_b64,
            "category": category
        }
        response = requests.post(
            f"{GPU_SERVER_URL}/tryon",
            json=payload,
            timeout=600
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Inferensi FASHN-VTON gagal pada tahap {category}"
            )
        return response.json()["result_b64"]

    def process_tryon(
        self,
        user_id: str,
        person_image_url: str,
        top_item_id: str,
        bottom_item_id: str
    ) -> dict:
        """
        Mengorkestrasi seluruh proses virtual try-on dua tahap:
        Tahap 1 - Inferensi Tops
        Tahap 2 - Inferensi Bottoms menggunakan gambar intermediate
        """
        start_time = time.time()

        # Ambil URL gambar dari Firebase
        top_item = self.wardrobe_service.get_item_by_id(user_id, top_item_id)
        bottom_item = self.wardrobe_service.get_item_by_id(user_id, bottom_item_id)

        if not top_item or not bottom_item:
            raise HTTPException(
                status_code=404,
                detail="Item pakaian tidak ditemukan di lemari digital"
            )

        # Unduh ketiga gambar menggunakan requests.get(url).content
        person_bytes = self._download_image(person_image_url)
        top_bytes = self._download_image(top_item["imageUrl"])
        bottom_bytes = self._download_image(bottom_item["imageUrl"])

        # Resize ke maksimal 768px menggunakan image.thumbnail((768, 768))
        person_bytes = self._resize_image(person_bytes)
        top_bytes = self._resize_image(top_bytes)
        bottom_bytes = self._resize_image(bottom_bytes)

        # Encode ke Base64 menggunakan base64.b64encode().decode('utf-8')
        person_b64 = self._encode_to_base64(person_bytes)
        top_b64 = self._encode_to_base64(top_bytes)
        bottom_b64 = self._encode_to_base64(bottom_bytes)

        # ── TAHAP 1: Inferensi Tops ──
        top_result_b64 = self._run_inference(person_b64, top_b64, "tops")

        # Decode hasil tops sebagai gambar intermediate
        intermediate_bytes = self._decode_from_base64(top_result_b64)
        intermediate_b64 = self._encode_to_base64(intermediate_bytes)

        # ── TAHAP 2: Inferensi Bottoms menggunakan gambar intermediate ──
        final_result_b64 = self._run_inference(intermediate_b64, bottom_b64, "bottoms")

        # Decode hasil akhir
        final_bytes = self._decode_from_base64(final_result_b64)

        # Upload hasil ke Cloudinary
        tryon_id = str(uuid.uuid4())
        result_image_url = upload_image(
            final_bytes,
            folder=f"tryon/{user_id}",
            public_id=tryon_id
        )

        # Hitung waktu pemrosesan
        processing_time = round(time.time() - start_time, 2)
        created_at = datetime.utcnow().isoformat()

        # Simpan metadata ke Firebase Realtime Database
        tryon_data = {
            "tryon_id": tryon_id,
            "result_image_url": result_image_url,
            "top_item_id": top_item_id,
            "bottom_item_id": bottom_item_id,
            "processing_time_seconds": processing_time,
            "created_at": created_at
        }
        ref = get_db_reference(f"users/{user_id}/tryon/{tryon_id}")
        ref.set(tryon_data)

        return tryon_data

    def get_history(self, user_id: str) -> list:
        """
        Mengambil riwayat hasil virtual try-on
        dari Firebase Realtime Database menggunakan
        db.reference('users/{uid}/tryon').get()
        """
        ref = get_db_reference(f"users/{user_id}/tryon")
        data = ref.get()
        if not data:
            return []
        return list(data.values())

    def delete_result(self, user_id: str, tryon_id: str) -> bool:
        """
        Menghapus hasil virtual try-on dari Firebase
        berdasarkan tryon_id
        """
        ref = get_db_reference(f"users/{user_id}/tryon/{tryon_id}")
        existing = ref.get()
        if not existing:
            return False
        ref.delete()
        return True
