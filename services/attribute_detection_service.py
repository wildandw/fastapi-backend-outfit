from PIL import Image
from io import BytesIO
from colorthief import ColorThief
import numpy as np
from transformers import CLIPProcessor, CLIPModel
import torch


class AttributeDetectionService:

    # =====================================================
    # CLOTHING TYPE KNOWLEDGE BASE
    # =====================================================

    CLOTHING_TYPES = [

        # ---------- Tops ----------
        "t shirt",
        "shirt",
        "polo shirt",
        "hoodie",
        "sweater",
        "cardigan",
        "jacket",
        "blazer",
        "blouse",

        # ---------- Bottoms ----------
        "jeans",
        "chino pants",
        "cargo pants",
        "trousers",
        "jogger pants",
        "shorts",
        "skirt"
    ]

    TOP_TYPES = {
        "t shirt",
        "shirt",
        "polo shirt",
        "hoodie",
        "sweater",
        "cardigan",
        "jacket",
        "blazer",
        "blouse"
    }

    BOTTOM_TYPES = {
        "jeans",
        "chino pants",
        "cargo pants",
        "trousers",
        "jogger pants",
        "shorts",
        "skirt"
    }

    # =====================================================
    # STYLE LABEL
    # =====================================================

    STYLE_LABELS = [
        "casual",
        "formal",
        "sporty",
        "streetwear"
    ]


    # =====================================================
    # OCCASION LABEL
    # (multi-label)
    # =====================================================

    OCCASION_LABELS = [
        "campus",
        "work",
        "hangout",
        "sport",
        "travel"
    ]

    # =====================================================
    # COLOR MAP
    # =====================================================

    COLOR_MAP = {

        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "grey": (128, 128, 128),
        "beige": (245, 245, 220),
        "navy": (0, 0, 128),

        "blue": (0, 0, 255),
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "yellow": (255, 255, 0),

        "brown": (139, 69, 19),
        "pink": (255, 192, 203),
        "purple": (128, 0, 128)
    }

    # =====================================================
    # INIT MODEL
    # =====================================================

    def __init__(self):

        model_name = "openai/clip-vit-base-patch32"

        self.model = CLIPModel.from_pretrained(model_name)

        self.processor = CLIPProcessor.from_pretrained(model_name)

    # =====================================================
    # VALIDATE CLOTHING
    # =====================================================

    def validate_clothing(self, image_bytes: bytes):

        clothing_type, confidence = self.detect_clothing_type(
            image_bytes
        )

        return {

            "is_clothing": confidence >= 0.35,

            "confidence": confidence,

            "detected_type": clothing_type

        }

    # =====================================================
    # DETECT DOMINANT COLOR
    # =====================================================

    def detect_color(self, image_bytes: bytes):

        try:

            ct = ColorThief(
                BytesIO(image_bytes)
            )

            dominant_rgb = ct.get_color(
                quality=1
            )

            return self._rgb_to_color_name(
                dominant_rgb
            )

        except Exception:

            return "unknown"

    # =====================================================
    # RGB TO COLOR NAME
    # =====================================================

    def _rgb_to_color_name(self, rgb):

        min_distance = float("inf")

        closest = "unknown"

        for name, color in self.COLOR_MAP.items():

            distance = np.sqrt(
                sum(
                    (a - b) ** 2
                    for a, b in zip(rgb, color)
                )
            )

            if distance < min_distance:

                min_distance = distance

                closest = name

        return closest

    # =====================================================
    # GENERATE PROMPT
    # =====================================================

    def _build_prompts(self, labels):

        prompts = []

        for label in labels:

            if label in self.CLOTHING_TYPES:

                prompts.append(
                    f"a photo of a {label}"
                )

            elif label in self.STYLE_LABELS:

                prompts.append(
                    f"a {label} clothing style"
                )

            else:

                prompts.append(
                    f"a clothing item suitable for {label}"
                )

        return prompts
    
    # =====================================================
    # CLASSIFY WITH CLIP
    # =====================================================

    def _classify_with_clip(
        self,
        image_bytes: bytes,
        labels: list
    ):

        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        prompts = self._build_prompts(labels)

        inputs = self.processor(
            text=prompts,
            images=image,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():

            outputs = self.model(**inputs)

            logits = outputs.logits_per_image

            probs = logits.softmax(dim=1)[0]

        best_index = torch.argmax(probs).item()

        return (
            labels[best_index],
            float(probs[best_index])
        )
    
    # =====================================================
    # DETECT CLOTHING TYPE
    # =====================================================

    def detect_clothing_type(
        self,
        image_bytes: bytes
    ):

        clothing_type, confidence = self._classify_with_clip(
            image_bytes,
            self.CLOTHING_TYPES
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

        # -------------------------------
        # Deteksi Warna
        # -------------------------------
        color = self.detect_color(
            image_bytes
        )

        # -------------------------------
        # Deteksi Jenis Pakaian
        # -------------------------------
        clothing_type, cat_conf = (
            self.detect_clothing_type(
                image_bytes
            )
        )

        category = self.get_category_from_type(
            clothing_type
        )

        # -------------------------------
        # Deteksi Style
        # -------------------------------
        style, sty_conf = (
            self._classify_with_clip(
                image_bytes,
                self.STYLE_LABELS
            )
        )


        # -------------------------------
        # Deteksi Occasion
        # -------------------------------
        occasion, occ_conf = (
            self._classify_with_clip(
                image_bytes,
                self.OCCASION_LABELS
            )
        )

        # -------------------------------
        # Hitung rata-rata confidence
        # -------------------------------
        avg_confidence = round(
            (
                cat_conf +
                sty_conf +
                occ_conf
            ) / 3,
            4
        )

        # =====================================================
        # Hasil Attribute Detection
        # =====================================================

        return {

            "color": color.capitalize(),

            "category": category,

            "detected_type": clothing_type.title(),

            "style": style.title(),

            "occasion": occasion.title(),

            "confidence": avg_confidence
        }