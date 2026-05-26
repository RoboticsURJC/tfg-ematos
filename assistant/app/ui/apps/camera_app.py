import cv2

from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

from app.ui.apps.base_app import BaseApp


class CameraApp(BaseApp):

    def __init__(self, controller=None, engine=None):
        super().__init__(controller, engine)

        self.app_name = "camera"

        self.cap = cv2.VideoCapture(0)

        self.label = QLabel("📷 Cámara")
        self.view = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.view)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def update(self):

        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, _ = rgb.shape

        img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)

        self.view.setPixmap(QPixmap.fromImage(img))

    def on_close(self):
        self.cap.release()
