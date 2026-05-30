import requests

from services.log_service import add_log


FACE_URL = "http://localhost:5000"


class FaceService:

    @staticmethod
    def recognize(image: str):

        try:

            r = requests.post(
                f"{FACE_URL}/recognize",
                json={"image": image},
                timeout=30
            )

            data = r.json()

            add_log("recognition", "Face recognition executed")

            return data

        except Exception as e:

            add_log("recognition", f"ERROR recognize: {str(e)}")

            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def register(name: str, images: list):

        try:

            r = requests.post(
                f"{FACE_URL}/register",
                json={
                    "name": name,
                    "images": images
                },
                timeout=60
            )

            data = r.json()

            add_log("recognition", f"User registered: {name}")

            return data

        except Exception as e:

            add_log("recognition", f"ERROR register: {str(e)}")

            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def memories(user: str):

        try:

            r = requests.get(
                f"{FACE_URL}/memories/{user}",
                timeout=10
            )

            return r.json()

        except Exception as e:

            add_log("recognition", f"ERROR memories: {str(e)}")

            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def remember(user: str, content: str):

        try:

            r = requests.post(
                f"{FACE_URL}/remember",
                json={
                    "user": user,
                    "content": content
                },
                timeout=10
            )

            return r.json()

        except Exception as e:

            add_log("recognition", f"ERROR remember: {str(e)}")

            return {"status": "ERROR", "error": str(e)}