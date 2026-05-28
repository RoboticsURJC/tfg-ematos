# app/core/camera_manager.py

import cv2

from app.core.logger import logger


class CameraManager:

    _instance = None

    def __init__(self):

        self.cap = None

    # =========================================
    # SINGLETON
    # =========================================
    @classmethod
    def get(cls):

        if cls._instance is None:
            cls._instance = CameraManager()

        return cls._instance

    # =========================================
    # OPEN CAMERA
    # =========================================
    def open(self):

        # ya abierta
        if self.cap is not None and self.cap.isOpened():
            return self.cap

        logger.info("📷 Abriendo cámara compartida")

        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        return self.cap

    # =========================================
    # READ
    # =========================================
    def read(self):

        if self.cap is None:
            self.open()

        return self.cap.read()

    # =========================================
    # RELEASE
    # =========================================
    def release(self):

        if self.cap is not None:

            logger.info("📷 Liberando cámara")

            self.cap.release()
            self.cap = None
            