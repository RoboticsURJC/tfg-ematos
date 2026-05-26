# app/robot/vision/camera_service.py

import cv2


class CameraService:
    """
    Cámara central del robot.
    """

    def __init__(self, device=0):

        self.cap = cv2.VideoCapture(device)

        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara")

        self.current_frame = None

    # =========================================================
    # READ FRAME
    # =========================================================

    def read(self):

        ret, frame = self.cap.read()

        if not ret:
            return None

        self.current_frame = frame

        return frame

    # =========================================================
    # RELEASE
    # =========================================================

    def release(self):

        if self.cap:
            self.cap.release()
