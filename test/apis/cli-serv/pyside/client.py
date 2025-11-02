import sys
import base64
import json
import numpy as np
import requests
import os
import cv2
from picamera2 import Picamera2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QDialog, QLineEdit, QProgressBar
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal


# ----- Cargar configuración -----
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

SERVER_URL = config["server_url"]


# ----- Hilo de trabajo para reconocimiento -----
class Worker(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, server_url, image_b64):
        super().__init__()
        self.server_url = server_url
        self.image_b64 = image_b64

    def run(self):
        try:
            response = requests.post(
                f"{self.server_url}/recognize",
                json={"image": self.image_b64},
                timeout=5
            )
            if response.ok:
                self.result_signal.emit(response.json())
            else:
                self.error_signal.emit("Error del servidor")
        except requests.exceptions.RequestException:
            self.error_signal.emit("No se pudo conectar al servidor")


# ----- Ventana emergente de progreso -----
class ProgressPopup(QDialog):
    def __init__(self, message="Procesando..."):
        super().__init__()
        self.setWindowTitle("Analizando rostro")
        self.setFixedSize(350, 120)
        self.setStyleSheet("""
            background-color: #2c3e50;
            color: white;
            font-family: Arial;
            font-size: 14px;
        """)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminado
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #4CAF50;
                border-radius: 5px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                margin: 1px;
                border-radius: 3px;
            }
        """)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)


# ----- Diálogo de registro -----
class RegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registro de Usuario")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #34495e; color: white; font-family: Arial;")

        layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del usuario")
        layout.addWidget(QLabel("Introduce el nombre del usuario:"))
        layout.addWidget(self.name_input)

        self.register_btn = QPushButton("Registrar")
        layout.addWidget(self.register_btn)

        self.setLayout(layout)
        self.registered_name = None
        self.register_btn.clicked.connect(self.try_register)

    def try_register(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío")
            return
        self.registered_name = name
        self.accept()


# ----- Aplicación principal -----
class ClientApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Client")
        self.setFixedSize(640, 520)
        self.setStyleSheet("background-color: #2c3e50;")

        # Inicializar cámara
        self.picam2 = Picamera2()
        self.picam2.start()
        self.current_frame = None

        # Widgets
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            border: 2px solid #333;
            border-radius: 10px;
            background-color: #222;
        """)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")

        self.login_btn = QPushButton("🔑 Iniciar sesión")
        self.register_btn = QPushButton("🧍 Registrar usuario")

        button_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """
        self.login_btn.setStyleSheet(button_style)
        self.register_btn.setStyleSheet(button_style)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(self.image_label)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.register_btn)
        layout.addWidget(self.result_label)
        layout.setStretch(0,1)
        layout.setStretch(1,0)
        layout.setStretch(2,0)
        layout.setStretch(3,0)
        layout.setStretch(4,0)

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
            rgb = cv2.flip(frame, 1)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(img).scaled(self.image_label.width(), self.image_label.height(), 
                                                   Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.current_frame = frame

    def capture_and_send(self):
        if self.current_frame is None:
            self.result_label.setStyleSheet("color: white; font-weight: bold")
            self.result_label.setText("Cámara no lista")
            return

        # Ventana emergente de progreso
        self.progress_popup = ProgressPopup("Iniciando sesión...")
        self.progress_popup.show()

        # Reducir y codificar imagen
        frame_resized = cv2.resize(self.current_frame, (320, 240))
        _, buffer = cv2.imencode(".jpg", frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
        img_str = base64.b64encode(buffer).decode("utf-8")

        # Lanzar hilo
        self.worker = Worker(SERVER_URL, img_str)
        self.worker.result_signal.connect(self.on_recognition_result)
        self.worker.error_signal.connect(self.on_recognition_error)
        self.worker.start()

    def on_recognition_result(self, data):
        self.progress_popup.close()

        names = data.get("recognized", [])
        if names:
            if "Desconocido" in names:
                QMessageBox.warning(self, "Inicio fallido", "Usuario desconocido.")
                self.result_label.setText("Inicio fallido")
            else:
                self.result_label.setText(f"Bienvenid@ {', '.join(names)}!")
        else:
            self.result_label.setText("No se reconoció ningún rostro")
        self.result_label.setStyleSheet("color: white; font-weight: bold")

    def on_recognition_error(self, message):
        self.progress_popup.close()
        self.result_label.setStyleSheet("color: #ff5555; font-weight: bold;")
        self.result_label.setText(message)

    def start_registration(self):
        dialog = RegistrationDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        name = dialog.registered_name

        images = []
        for i in range(5):
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


# ----- Ejecutar aplicación -----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ClientApp()
    client.show()
    sys.exit(app.exec_())
