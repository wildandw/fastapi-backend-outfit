from io import BytesIO
from PIL import Image

from services.clip_service import CLIPService


class ClothingValidator:

    def __init__(self, clip_service: CLIPService):

        self.clip_service = clip_service

        self.top_labels = [
            "a shirt",
            "a t shirt",
            "a blouse",
            "a hoodie",
            "a jacket"
        ]

        self.bottom_labels = [
            "pants",
            "jeans",
            "a skirt",
            "shorts"
        ]

    def validate(
        self,
        image_bytes: bytes,
        category: str
    ):

        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        labels = (
            self.top_labels +
            self.bottom_labels +
            [
                "a dog",
                "a cat",
                "a car",
                "food",
                "a person",
                "a phone"
            ]
        )

        predicted, confidence = self.clip_service.classify(
            image_bytes=image_bytes,
            labels=labels,
            prompts=labels
        )

        if category == "Tops":
            return predicted in self.top_labels

        if category == "Bottoms":
            return predicted in self.bottom_labels

        return False