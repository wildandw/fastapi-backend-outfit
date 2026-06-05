import os
import base64
import requests

from fastapi import HTTPException


GPU_SERVER_URL = os.getenv("GPU_SERVER_URL")


class RemoveBackgroundService:

    def _encode_to_base64(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    def _decode_from_base64(self, b64_string: str) -> bytes:
        return base64.b64decode(b64_string)

    def remove_background(self, image_bytes: bytes) -> bytes:
        """
        Mengirim gambar pakaian ke endpoint Colab BiRefNet
        untuk remove background
        """

        cloth_b64 = self._encode_to_base64(image_bytes)

        payload = {
            "cloth_b64": cloth_b64
        }

        try:

            response = requests.post(
                f"{GPU_SERVER_URL}/remove-background",
                json=payload,
                timeout=300
            )

            print("=================================")
            print("GPU URL:", GPU_SERVER_URL)
            print("Response status:", response.status_code)
            print("Response body:", response.text)
            print("=================================")

            if response.status_code != 200:

                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text

                raise HTTPException(
                    status_code=500,
                    detail=f"Remove background gagal: {error_detail}"
                )

            result_b64 = response.json()["result_b64"]

            return self._decode_from_base64(result_b64)

        except requests.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Gagal koneksi ke GPU server: {str(e)}"
            )