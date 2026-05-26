import os
import json
import base64
import sys
import cv2
import requests

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout,
    QMessageBox, QInputDialog,
    QProgressBar
)

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication

from app.robot.display.face_display import FaceDisplay
from app.core.logger import logger


config_path = os.path.join(os.path.dirname(__file__), "../../config/config.json")

with open(config_path, "r") as f:
    config = json.load(f)

SERVER_URL = config["server"]["recognition_url"]


# =========================
# WORKER
# =========================
class Worker(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, url, image):
        super().__init__()
        self.url = url
        self.image = image

    def run(self):
        try:
            r = requests.post(
                f"{self.url}/recognize",
                json={"image": self.image},
                timeout=10
            )

            if r.ok:
                self.result_signal.emit(r.json())
            else:
                self.error_signal.emit(str(r.status_code))

        except Exception as e:
            self.error_signal.emit(str(e))


# =========================
# LOGIN SCREEN
# =========================
class LoginScreen(QWidget):

    authenticated = pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()

        logger.info(" -> Iniciando Login Screen")

        self.controller = controller

        self.setWindowTitle("Login Facial")

        # display robot
        self.display = FaceDisplay(config_path=config_path)
        self.display.start()

        # camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Cámara no disponible")

        self.current_frame = None

        # UI
        self.title = QLabel("🔐 Reconocimiento facial")
        self.title.setAlignment(Qt.AlignCenter)

        self.camera = QLabel()
        self.status = QLabel("Esperando usuario...")

        self.btn_login = QPushButton("Iniciar sesión")
        self.btn_login.clicked.connect(self.login)

        self.btn_exit = QPushButton("Salir")
        self.btn_exit.clicked.connect(self.close_app)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.camera)
        layout.addWidget(self.status)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_exit)

        self.setLayout(layout)

        # loop cámara
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    # -------------------------
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        self.current_frame = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, _ = rgb.shape
        img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)

        self.camera.setPixmap(QPixmap.fromImage(img))

    # -------------------------
    def login(self):

        if self.current_frame is None:
            return

        self.status.setText("Reconociendo...")

        frame = cv2.resize(self.current_frame, (320, 240))
        _, buffer = cv2.imencode(".jpg", frame)

        img_b64 = base64.b64encode(buffer).decode()

        self.worker = Worker(SERVER_URL, img_b64)
        self.worker.result_signal.connect(self.on_result)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def close_app(self):
        self.timer.stop()

        if self.cap:
            self.cap.release()
        
        self.display.stop()
        
        QApplication.quit()
        sys.exit(0)

    # -------------------------
    def on_result(self, data):

        names = data.get("recognized", [])

        if names and names[0] != "Desconocido":

            user = names[0]

            logger.info(f" -> Usuario {user} logeado")

            self.display.set_estado(f"Hola {user}")
            self.authenticated.emit(user)

        else:
            self.status.setText("No reconocido")

    # -------------------------
    def on_error(self, msg):
        self.status.setText("Error conexión")

    # -------------------------
    def closeEvent(self, event):
        self.cap.release()
        self.display.stop()
        event.accept()