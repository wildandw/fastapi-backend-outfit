from PIL import Image
from io import BytesIO
from colorthief import ColorThief
import numpy as np
from transformers import CLIPProcessor, CLIPModel
import torch


class AttributeDetectionService:

    # =====================================================
    # DETEKSI JENIS PAKAIAN
    # =====================================================

    CLOTHING_TYPES = [
        "t shirt",
        "shirt",
        "polo shirt",
        "hoodie",
        "jacket",
        "blazer",

        "jeans",
        "pants",
        "trousers",
        "shorts",
        "skirt"
    ]

    TOP_TYPES = {
        "t shirt",
        "shirt",
        "polo shirt",
        "hoodie",
        "jacket",
        "blazer"
    }

    BOTTOM_TYPES = {
        "jeans",
        "pants",
        "trousers",
        "shorts",
        "skirt"
    }

    STYLE_LABELS = [
        "casual",
        "formal",
        "sporty",
        "streetwear"
    ]

    PATTERN_LABELS = [
        "solid",
        "stripe",
        "floral",
        "plaid",
        "graphic",
        "abstract"
    ]

    ACTIVITY_LABELS = [
        "hangout",
        "work",
        "sport",
        "formal event",
        "daily"
    ]

    # =====================================================
    # COLOR MAP
    # =====================================================

    COLOR_MAP = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "blue": (0, 0, 255),
        "green": (0, 128, 0),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "pink": (255, 192, 203),
        "brown": (139, 69, 19),
        "grey": (128, 128, 128),
        "navy": (0, 0, 128),
        "beige": (245, 245, 220),
    }

    def __init__(self):

        self.model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32"
        )

        self.processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )

    # =====================================================
    # DETECT COLOR
    # =====================================================

    def detect_color(self, image_bytes: bytes) -> str:

        try:

            ct = ColorThief(BytesIO(image_bytes))

            dominant_rgb = ct.get_color(
                quality=1
            )

            return self._rgb_to_color_name(
                dominant_rgb
            )

        except Exception:

            return "unknown"

    # =====================================================
    # RGB -> COLOR NAME
    # =====================================================

    def _rgb_to_color_name(
        self,
        rgb: tuple
    ) -> str:

        min_distance = float("inf")
        closest_color = "unknown"

        for name, color_rgb in self.COLOR_MAP.items():

            distance = np.sqrt(
                sum(
                    (a - b) ** 2
                    for a, b in zip(rgb, color_rgb)
                )
            )

            if distance < min_distance:

                min_distance = distance
                closest_color = name

        return closest_color

    # =====================================================
    # CLIP CLASSIFICATION
    # =====================================================

    def _classify_with_clip(
        self,
        image_bytes: bytes,
        labels: list
    ):

        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        text_labels = []

        for label in labels:

            if label in [
                "jeans",
                "pants",
                "trousers",
                "shorts",
                "skirt"
            ]:

                text_labels.append(
                    f"a photo of a person wearing {label}"
                )

            else:

                text_labels.append(
                    f"a photo of a person wearing a {label}"
                )

        inputs = self.processor(
            text=text_labels,
            images=image,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():

            outputs = self.model(
                **inputs
            )

            logits = outputs.logits_per_image

            probs = logits.softmax(
                dim=1
            )

        best_idx = probs.argmax().item()

        confidence = probs[
            0
        ][
            best_idx
        ].item()

        return (
            labels[best_idx],
            round(confidence, 4)
        )

    # =====================================================
    # DETECT CLOTHING TYPE
    # =====================================================

    def detect_clothing_type(
        self,
        image_bytes: bytes
    ):

        clothing_type, confidence = (
            self._classify_with_clip(
                image_bytes,
                self.CLOTHING_TYPES
            )
        )

        return clothing_type, confidence

    # =====================================================
    # MAP TYPE -> CATEGORY
    # =====================================================

    def get_category_from_type(
        self,
        clothing_type: str
    ) -> str:

        if clothing_type in self.TOP_TYPES:
            return "Tops"

        if clothing_type in self.BOTTOM_TYPES:
            return "Bottoms"

        return "Unknown"

    # =====================================================
    # DETECT ATTRIBUTES
    # =====================================================

    def detect_attributes(
        self,
        image_bytes: bytes
    ) -> dict:

        color = self.detect_color(
            image_bytes
        )

        clothing_type, cat_conf = (
            self.detect_clothing_type(
                image_bytes
            )
        )

        category = self.get_category_from_type(
            clothing_type
        )

        style, sty_conf = (
            self._classify_with_clip(
                image_bytes,
                self.STYLE_LABELS
            )
        )

        pattern, pat_conf = (
            self._classify_with_clip(
                image_bytes,
                self.PATTERN_LABELS
            )
        )

        activities, act_conf = (
            self._classify_with_clip(
                image_bytes,
                self.ACTIVITY_LABELS
            )
        )

        avg_confidence = round(
            (
                cat_conf +
                sty_conf +
                pat_conf +
                act_conf
            ) / 4,
            4
        )

        return {

            "color": color.capitalize(),

            "category": category,

            "detected_type": clothing_type.capitalize(),

            "style": style.capitalize(),

            "pattern": pattern.capitalize(),

            "activities": activities.capitalize(),

            "confidence": avg_confidence
        }