import cloudinary
import cloudinary.uploader
import os
from io import BytesIO

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(image_bytes: bytes, folder: str, public_id: str = None) -> str:
    """
    Mengunggah gambar ke Cloudinary menggunakan
    cloudinary.uploader.upload() dan mengembalikan URL publik
    """
    result = cloudinary.uploader.upload(
        image_bytes,
        folder=folder,
        public_id=public_id,
        overwrite=True,
        resource_type="image"
    )
    return result["secure_url"]

def delete_image(public_id: str) -> bool:
    """
    Menghapus gambar dari Cloudinary berdasarkan public_id
    """
    result = cloudinary.uploader.destroy(public_id)
    return result["result"] == "ok"
