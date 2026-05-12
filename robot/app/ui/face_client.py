import sys
import os
import json
import base64
import cv2
import logging

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QDialog, QProgressBar
)

from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from app.ui.display import FaceDisplay


# =========================
# CONFIG
# =========================
config_path = os.path.join(
    os.path.dirname(__file__),
    "../config/config.json"
)

with open(config_path, "r") as f:
    config = json.load(f)

SERVER_URL = config["server"]["recognition_url"]


# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FaceClient")


# =========================
# WORKER (API CALL)
# =========================
class Worker(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, server_url, image):
        super().__init__()
        self.server_url = server_url
        self.image = image

    def run(self):
        try:
            import requests

            r = requests.post(
                f"{self.server_url}/recognize",
                json={"image": self.image},
                timeout=10
            )

            if r.ok:
                self.result_signal.emit(r.json())
            else:
                self.error_signal.emit("Error del servidor")

        except Exception as e:
            self.error_signal.emit(f"Sin conexión: {e}")


# =========================
# POPUP
# =========================
class ProgressPopup(QDialog):
    def __init__(self, text="Procesando..."):
        super().__init__()

        self.setWindowTitle("Face AI")
        self.setFixedSize(300, 120)
        self.setModal(True)

        layout = QVBoxLayout()

        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)

        self.bar = QProgressBar()
        self.bar.setRange(0, 0)

        layout.addWidget(self.label)
        layout.addWidget(self.bar)

        self.setLayout(layout)


# =========================
# FACE CLIENT
# =========================
class FaceClient(QWidget):

    def __init__(self, on_authenticated):
        super().__init__()

        self.server_url = SERVER_URL
        self.on_authenticated = on_authenticated

        self.setWindowTitle("Face Client")
        self.setFixedSize(640, 520)

        # =========================
        # DISPLAY FÍSICO (SPI)
        # =========================
        self.display = FaceDisplay(config_path=config_path)
        self.display.set_estado("Sistema iniciado")

        import threading
        threading.Thread(
            target=self.display.start,
            daemon=True
        ).start()

        # =========================
        # CÁMARA
        # =========================
        self.cap = cv2.VideoCapture(0)
        self.current_frame = None

        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara")

        # =========================
        # UI
        # =========================
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)

        self.result_label = QLabel("Esperando...")
        self.result_label.setAlignment(Qt.AlignCenter)

        self.btn_login = QPushButton("Login")
        self.btn_register = QPushButton("Registrar")

        layout = QVBoxLayout()
        layout.addWidget(self.image)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_register)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

        # =========================
        # EVENTS
        # =========================
        self.btn_login.clicked.connect(self.login)
        self.btn_register.clicked.connect(self.register)

        # =========================
        # CAMERA TIMER
        # =========================
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    # =========================
    # CAMERA LOOP
    # =========================
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        self.current_frame = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)

        self.image.setPixmap(
            QPixmap.fromImage(img).scaled(
                320, 240,
                Qt.KeepAspectRatio
            )
        )

    # =========================
    # LOGIN
    # =========================
    def login(self):

        if self.current_frame is None:
            self.result_label.setText("Cámara no lista")
            return

        self.display.set_estado("Reconociendo rostro...")

        self.popup = ProgressPopup("Analizando...")
        self.popup.show()

        frame = cv2.resize(self.current_frame, (320, 240))
        _, buffer = cv2.imencode(".jpg", frame)

        img = base64.b64encode(buffer).decode()

        self.worker = Worker(self.server_url, img)
        self.worker.result_signal.connect(self.on_result)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    # =========================
    # RESULTADO
    # =========================
    def on_result(self, data):

        self.popup.close()

        names = data.get("recognized", [])

        if names:

            user = names[0]

            self.result_label.setText(f"Bienvenido {user}")
            self.display.set_estado(f"Bienvenido {user}")

            # 🔥 EVENTO LIMPIO HACIA EL CEREBRO
            self.on_authenticated(user)

        else:

            self.result_label.setText("No reconocido")
            self.display.set_estado("Intruso detectado")

    # =========================
    # ERROR
    # =========================
    def on_error(self, msg):

        self.popup.close()

        self.result_label.setText(msg)
        self.display.set_estado("Error de conexión")

    # =========================
    # REGISTER (FUTURO)
    # =========================
    def register(self):
        self.result_label.setText("Registro no implementado")

    # =========================
    # CLOSE
    # =========================
    def closeEvent(self, event):

        if self.cap:
            self.cap.release()

        event.accept()