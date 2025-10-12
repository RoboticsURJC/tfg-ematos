# client_qt.py
import sys
import base64
import json
import requests
import cv2
from picamera2 import Picamera2
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QInputDialog
)
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer


# Cargar configuración
with open("config.json") as f:
    config = json.load(f)
SERVER_URL = config["server_url"]


class ClientApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Client")
        self.setFixedSize(640, 520)

        # Inicializar cámara
        self.picam2 = Picamera2()
        self.picam2.start()
        self.current_frame = None

        # UI
        self.image_label = QLabel(alignment=0x84)  # centrar
        self.result_label = QLabel("", alignment=0x84)
        self.login_btn = QPushButton("🔑 Iniciar sesión")
        self.register_btn = QPushButton("🧍 Registrar usuario")

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.register_btn)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

        # Conectar botones
        self.login_btn.clicked.connect(self.capture_and_send)
        self.register_btn.clicked.connect(self.start_registration)

        # Refresco de cámara
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        frame = self.picam2.capture_array()
        if frame is not None:
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(img).scaled(640, 480))
            self.current_frame = frame

    def capture_and_send(self):
        if self.current_frame is None:
            self.result_label.setText("Cámara no lista")
            return

        _, buffer = cv2.imencode(".jpg", self.current_frame)
        img_str = base64.b64encode(buffer).decode("utf-8")

        try:
            response = requests.post(f"{SERVER_URL}/recognize", json={"image": img_str}, timeout=5)
            if response.ok:
                names = response.json().get("recognized", [])
                if names:
                    self.result_label.setText(f"Reconocido: {', '.join(names)}")
                else:
                    self.result_label.setText("No se reconoció ningún rostro")
            else:
                self.result_label.setText("Error del servidor")
        except requests.exceptions.RequestException:
            self.result_label.setText("No se pudo conectar al servidor")

    def start_registration(self):
        name, ok = QInputDialog.getText(self, "Registro", "Introduce el nombre del usuario:")
        if not ok or not name:
            return

        images = []
        for i in range(3):
            QMessageBox.information(self, "Registro", f"Prepárate para la foto {i + 1}")
            frame = self.current_frame
            if frame is not None:
                _, buffer = cv2.imencode(".jpg", frame)
                img_str = base64.b64encode(buffer).decode("utf-8")
                images.append(img_str)
            else:
                QMessageBox.critical(self, "Error", "No se pudo capturar el frame")
                return

        try:
            response = requests.post(f"{SERVER_URL}/register", json={"name": name, "images": images}, timeout=10)
            if response.ok:
                QMessageBox.information(self, "Registro", f"Usuario {name} registrado con éxito ✅")
            else:
                QMessageBox.warning(self, "Error", "El usuario no pudo registrarse en el servidor")
        except requests.exceptions.RequestException:
            QMessageBox.critical(self, "Error", "No se pudo conectar al servidor")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ClientApp()
    client.show()
    sys.exit(app.exec())
