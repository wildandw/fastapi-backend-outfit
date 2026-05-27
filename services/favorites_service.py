import uuid
import requests
import base64
from datetime import datetime
from io import BytesIO

from utils.firebase import get_db_reference
from utils.cloudinary_helper import upload_image, delete_image
from fastapi import HTTPException


class FavoritesService:

    def add_favorite(self, user_id: str, request) -> dict:
        """
        Menyimpan favorit ke Firebase dan foto ke Cloudinary.
        Mendukung dua jenis favorit:
        - type: 'tryon'        → dari hasil virtual try-on
        - type: 'outfit'       → dari pasangan outfit rekomendasi
        """
        favorite_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        # Unduh gambar dari URL sumber menggunakan requests.get()
        image_response = requests.get(request.image_url, timeout=30)
        if image_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Gagal mengunduh gambar untuk disimpan ke favorit"
            )
        image_bytes = image_response.content

        # Unggah foto ke Cloudinary menggunakan cloudinary.uploader.upload()
        # ke folder favorites/{user_id}
        saved_image_url = upload_image(
            image_bytes,
            folder=f"favorites/{user_id}",
            public_id=favorite_id
        )

        # Bangun metadata favorit
        favorite_data = {
            "favorite_id": favorite_id,
            "type": request.favorite_type,       # 'tryon' atau 'outfit'
            "reference_id": request.reference_id, # tryon_id atau recommendation_id
            "image_url": saved_image_url,          # URL foto di Cloudinary
            "top_item_id": request.top_item_id,
            "bottom_item_id": request.bottom_item_id,
            "note": request.note or "",
            "created_at": created_at
        }

        # Simpan metadata ke Firebase Realtime Database menggunakan
        # db.reference('users/{uid}/favorites/{favorite_id}').set()
        ref = get_db_reference(f"users/{user_id}/favorites/{favorite_id}")
        ref.set(favorite_data)

        return favorite_data

    def get_all_favorites(self, user_id: str) -> list:
        """
        Mengambil seluruh daftar favorit pengguna dari Firebase
        menggunakan db.reference('users/{uid}/favorites').get()
        dan mengembalikan dalam bentuk list yang diurutkan
        berdasarkan created_at terbaru
        """
        ref = get_db_reference(f"users/{user_id}/favorites")
        data = ref.get()
        if not data:
            return []
        favorites = list(data.values())

        # Urutkan berdasarkan created_at descending (terbaru dulu)
        favorites.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return favorites

    def get_favorite_by_id(self, user_id: str, favorite_id: str) -> dict:
        """
        Mengambil satu item favorit berdasarkan favorite_id
        menggunakan db.reference('users/{uid}/favorites/{favorite_id}').get()
        """
        ref = get_db_reference(f"users/{user_id}/favorites/{favorite_id}")
        return ref.get()

    def delete_favorite(self, user_id: str, favorite_id: str) -> bool:
        """
        Menghapus item favorit dari Firebase menggunakan
        db.reference('users/{uid}/favorites/{favorite_id}').delete()
        dan menghapus foto dari Cloudinary menggunakan
        cloudinary.uploader.destroy(public_id=favorite_id)
        """
        ref = get_db_reference(f"users/{user_id}/favorites/{favorite_id}")
        existing = ref.get()
        if not existing:
            return False

        # Hapus foto dari Cloudinary
        delete_image(f"favorites/{user_id}/{favorite_id}")

        # Hapus metadata dari Firebase
        ref.delete()
        return True

    def is_favorited(self, user_id: str, reference_id: str) -> bool:
        """
        Memeriksa apakah suatu item sudah disimpan ke favorit
        dengan mencari reference_id di seluruh data favorit pengguna
        """
        favorites = self.get_all_favorites(user_id)
        return any(
            fav.get("reference_id") == reference_id
            for fav in favorites
        )
