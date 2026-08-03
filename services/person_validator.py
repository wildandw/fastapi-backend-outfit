from io import BytesIO
from PIL import Image
from ultralytics import YOLO

class PersonValidator:

    def __init__(self):
        self.model = None

    def _load_model(self):
        if self.model is None:
            self.model = YOLO("yolov8n.pt")

    def validate(self, image_bytes: bytes):
        self._load_model()

        image = Image.open(BytesIO(image_bytes))
        results = self.model(image)

        person_count = 0

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            if class_id == 0:
                person_count += 1

        return person_count