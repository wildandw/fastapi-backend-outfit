from io import BytesIO

from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch


class CLIPService:

    MODEL_NAME = "openai/clip-vit-base-patch32"

    _instance = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):

        if getattr(self, "_initialized", False):
            return

        print("================================")
        print("LOADING SHARED CLIP MODEL")
        print("================================")

        self.model = CLIPModel.from_pretrained(
            self.MODEL_NAME
        )

        self.processor = CLIPProcessor.from_pretrained(
            self.MODEL_NAME
        )

        self.model.eval()

        self._initialized = True

        print("================================")
        print("SHARED CLIP MODEL READY")
        print("================================")

    def classify(
        self,
        image_bytes: bytes,
        labels: list,
        prompts: list = None
    ):

        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        if prompts is None:
            prompts = labels

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