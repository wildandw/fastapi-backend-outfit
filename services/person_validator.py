from io import BytesIO
from PIL import Image
from ultralytics import YOLO

class PersonValidator:

    def __init__(self):

        self.model = YOLO("yolov8n.pt")

    def validate(self, image_bytes: bytes):

        image = Image.open(
            BytesIO(image_bytes)
        )

        results = self.model(image)

        person_count = 0

        for box in results[0].boxes:

            class_id = int(box.cls[0])

            if class_id == 0:
                person_count += 1

        return person_count