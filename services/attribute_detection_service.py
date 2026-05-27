from PIL import Image
from io import BytesIO
from colorthief import ColorThief
import numpy as np
from transformers import CLIPProcessor, CLIPModel
import torch


class AttributeDetectionService:

    # Label kategori untuk CLIP model
    CATEGORY_LABELS = ["tops", "bottoms", "dress", "outerwear", "shoes"]
    STYLE_LABELS = ["casual", "formal", "sporty", "streetwear", "traditional"]
    PATTERN_LABELS = ["solid", "stripe", "floral", "plaid", "graphic", "abstract"]
    ACTIVITY_LABELS = ["hangout", "work", "sport", "formal event", "daily"]

    # Mapping warna RGB ke nama warna
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
        """
        Memuat CLIP model dari HuggingFace untuk
        klasifikasi kategori, style, pola, dan aktivitas
        """
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    def detect_color(self, image_bytes: bytes) -> str:
        """
        Mendeteksi warna dominan gambar menggunakan ColorThief
        kemudian mencocokkan ke nama warna terdekat
        menggunakan perhitungan jarak Euclidean
        """
        ct = ColorThief(BytesIO(image_bytes))
        dominant_rgb = ct.get_color(quality=1)
        return self._rgb_to_color_name(dominant_rgb)

    def _rgb_to_color_name(self, rgb: tuple) -> str:
        """
        Mengkonversi nilai RGB ke nama warna terdekat
        menggunakan perhitungan jarak Euclidean
        """
        min_distance = float("inf")
        closest_color = "unknown"
        for name, color_rgb in self.COLOR_MAP.items():
            distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb, color_rgb)))
            if distance < min_distance:
                min_distance = distance
                closest_color = name
        return closest_color

    def _classify_with_clip(self, image_bytes: bytes, labels: list) -> tuple:
        """
        Mengklasifikasikan gambar menggunakan CLIP model
        dengan menghitung cosine similarity antara
        gambar dan deskripsi teks setiap label
        """
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        text_labels = [f"a photo of {label} clothing" for label in labels]
        inputs = self.processor(
            text=text_labels,
            images=image,
            return_tensors="pt",
            padding=True
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits_per_image
            probs = logits.softmax(dim=1)
        best_idx = probs.argmax().item()
        confidence = probs[0][best_idx].item()
        return labels[best_idx], round(confidence, 4)

    def detect_attributes(self, image_bytes: bytes) -> dict:
        """
        Mendeteksi seluruh atribut pakaian secara otomatis:
        - Warna menggunakan ColorThief + Euclidean distance
        - Kategori menggunakan CLIP model
        - Style menggunakan CLIP model
        - Pola menggunakan CLIP model
        - Aktivitas menggunakan CLIP model
        Hasil dapat diedit oleh pengguna setelah deteksi
        """
        color = self.detect_color(image_bytes)
        category, cat_conf = self._classify_with_clip(image_bytes, self.CATEGORY_LABELS)
        style, sty_conf = self._classify_with_clip(image_bytes, self.STYLE_LABELS)
        pattern, pat_conf = self._classify_with_clip(image_bytes, self.PATTERN_LABELS)
        activities, act_conf = self._classify_with_clip(image_bytes, self.ACTIVITY_LABELS)
        avg_confidence = round((cat_conf + sty_conf + pat_conf + act_conf) / 4, 4)

        return {
            "color": color,
            "category": category.capitalize(),
            "style": style.capitalize(),
            "pattern": pattern.capitalize(),
            "activities": activities.capitalize(),
            "confidence": avg_confidence
        }
