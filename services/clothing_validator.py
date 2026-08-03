from io import BytesIO
from PIL import Image

from transformers import (
    CLIPProcessor,
    CLIPModel
)

import torch


class ClothingValidator:

    def __init__(self):

        self.model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32"
        )

        self.processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )

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

        inputs = self.processor(
            text=labels,
            images=image,
            return_tensors="pt",
            padding=True
        )

        outputs = self.model(**inputs)

        probs = (
            outputs.logits_per_image
            .softmax(dim=1)
        )

        best_idx = probs.argmax().item()

        predicted = labels[best_idx]

        if category == "Tops":
            return predicted in self.top_labels

        if category == "Bottoms":
            return predicted in self.bottom_labels

        return False