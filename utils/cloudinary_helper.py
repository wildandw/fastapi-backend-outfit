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

def upload_image(
    image_bytes: bytes,
    folder: str,
    public_id: str = None
):
    result = cloudinary.uploader.upload(
        image_bytes,
        folder=folder,
        public_id=public_id,
        overwrite=True,
        resource_type="image"
    )

    return {
        "image_url": result["secure_url"],
        "public_id": result["public_id"]
    }

def delete_image(public_id: str) -> bool:

    result = cloudinary.uploader.destroy(
        public_id
    )

    print(
        f"DELETE CLOUDINARY: {public_id}"
    )

    print(result)

    return result["result"] == "ok"
