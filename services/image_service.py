from PIL import Image
from io import BytesIO
from utils.cloudinary_helper import upload_image


class ImageService:


    def create_thumbnail(self, image_bytes: bytes, size: tuple = (512, 512)) -> bytes:
        """
        Membuat thumbnail menggunakan image.thumbnail()
        untuk mengoptimalkan ukuran file sebelum diunggah
        """
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail(size)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def upload_to_cloudinary(self, image_bytes: bytes, folder: str) -> str:
        """
        Mengunggah gambar ke Cloudinary
        menggunakan cloudinary.uploader.upload()
        dan mengembalikan URL publik gambar
        """
        return upload_image(image_bytes, folder=folder)

    def resize_for_tryon(self, image_bytes: bytes, max_size: int = 768) -> bytes:
        """
        Melakukan resize gambar ke maksimal 768px pada sisi terpanjang
        menggunakan image.thumbnail((768, 768)) sebelum
        dikirim ke OOTDiffusion Model
        """
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail((max_size, max_size))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
