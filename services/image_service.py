from PIL import Image
from io import BytesIO

from utils.cloudinary_helper import upload_image


class ImageService:

    def create_thumbnail(
        self,
        image_bytes: bytes,
        size: tuple = (512, 512)
    ) -> bytes:

        img = Image.open(BytesIO(image_bytes))

        img.thumbnail(size)

        buffer = BytesIO()

        img.save(buffer, format="PNG")

        return buffer.getvalue()

    def resize_image(
        self,
        image_bytes: bytes,
        max_size: int = 768
    ) -> bytes:

        img = Image.open(BytesIO(image_bytes))

        img.thumbnail((max_size, max_size))

        buffer = BytesIO()

        img.save(buffer, format="PNG")

        return buffer.getvalue()

    def upload_to_cloudinary(
        self,
        image_bytes: bytes,
        folder: str,
        public_id: str = None
    ):

        return upload_image(
            image_bytes,
            folder=folder,
            public_id=public_id
        )