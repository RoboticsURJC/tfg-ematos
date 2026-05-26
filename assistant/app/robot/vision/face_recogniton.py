# app/robot/vision/face_recognition.py

import base64
import requests
import cv2


class FaceRecognitionService:
    """
    Cliente hacia servidor de reconocimiento facial.
    """

    def __init__(self, server_url: str):

        self.server_url = server_url

    # =========================================================
    # RECOGNIZE
    # =========================================================

    def recognize(self, frame):

        try:

            frame = cv2.resize(frame, (320, 240))

            _, buffer = cv2.imencode(".jpg", frame)

            img_b64 = base64.b64encode(buffer).decode()

            r = requests.post(
                f"{self.server_url}/recognize",
                json={"image": img_b64},
                timeout=10
            )

            if r.ok:
                return r.json()

            return {"recognized": []}

        except Exception as e:

            print("[FACE ERROR]", e)

            return {"recognized": []}

    # =========================================================
    # REGISTER
    # =========================================================

    def register(self, name, images):

        try:

            payload = {
                "name": name,
                "images": images
            }

            r = requests.post(
                f"{self.server_url}/register",
                json=payload,
                timeout=20
            )

            return r.json() if r.ok else None

        except Exception as e:

            print("[REGISTER ERROR]", e)

            return None
