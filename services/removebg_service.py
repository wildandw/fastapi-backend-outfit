import os
import base64
import requests

from fastapi import HTTPException

# =====================================================
# RUNPOD CONFIG
# =====================================================
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

RUNPOD_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"


class RemoveBackgroundService:

    # =====================================================
    # BASE64
    # =====================================================

    def _encode_to_base64(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    def _decode_from_base64(self, b64_string: str) -> bytes:
        return base64.b64decode(b64_string)

    # =====================================================
    # REMOVE BACKGROUND
    # =====================================================

    def remove_background(self, image_bytes: bytes) -> bytes:
        """
        Mengirim gambar pakaian ke RunPod
        untuk proses remove background menggunakan BiRefNet.
        """

        cloth_b64 = self._encode_to_base64(image_bytes)

        payload = {
            "input": {
                "action": "remove-background",
                "cloth_b64": cloth_b64
            }
        }

        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }

        try:

            response = requests.post(
                RUNPOD_URL,
                headers=headers,
                json=payload,
                timeout=600
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"RunPod HTTP {response.status_code}"
                )

            data = response.json()

            print("================================")
            print("RUNPOD REMOVE BG RESPONSE")
            print(data)
            print("================================")

            # RunPod mengembalikan status FAILED meskipun HTTP 200
            if data.get("status") == "FAILED":
                raise HTTPException(
                    status_code=500,
                    detail=f"Remove background gagal: {data.get('error', 'Unknown error')}"
                )

            output = data.get("output", {})

            if "error" in output:
                raise HTTPException(
                    status_code=500,
                    detail=output["error"]
                )

            if "result_b64" not in output:
                raise HTTPException(
                    status_code=500,
                    detail=f"Response RunPod tidak berisi result_b64: {data}"
                )

            result_b64 = output["result_b64"]

            return self._decode_from_base64(result_b64)

        except requests.RequestException as e:

            raise HTTPException(
                status_code=500,
                detail=f"Gagal koneksi ke RunPod: {str(e)}"
            )