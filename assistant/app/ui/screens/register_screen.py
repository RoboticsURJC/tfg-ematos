
        
# app/ui/screens/register_screen.py

import os
import base64
import cv2
import requests

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QProgressBar,
    QLineEdit
)

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from app.core.camera_manager import CameraManager
from app.core.config import Config
from app.core.logger import logger


# =====================================================
# WORKER REGISTER (NO BLOQUEA UI)
# =====================================================
class RegisterWorker(QThread):

    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, name, images):
        super().__init__()

        self.url = url
        self.name = name
        self.images = images

    def run(self):

        try:
            r = requests.post(
                self.url,
                json={
                    "name": self.name,
                    "images": self.images
                },
                timeout=15
            )

            if r.ok:
                self.success.emit()
            else:
                self.error.emit(f"Error servidor: {r.status_code}")

        except Exception as e:
            self.error.emit(str(e))


# =====================================================
# REGISTER SCREEN
# =====================================================
class RegisterScreen(QWidget):

    def __init__(self, controller):

        super().__init__()

        self.controller = controller
        self.config = Config()

        self.setWindowTitle("Registro Facial")
        self.setMinimumSize(950, 750)
        self.setObjectName("registerScreen")
        
        logger.info("Iniciando registro de usuario")

        # =================================================
        # QSS
        # =================================================
        qss_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "themes",
            "register.qss"
        )

        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        # =================================================
        # CAMERA (COMPARTIDA)
        # =================================================
        CameraManager.get().open()

        self.frame = None

        # =================================================
        # FLOW
        # =================================================
        self.images = []
        self.step = 0

        self.steps_text = [
            "📷 Foto 1/3 — mira al frente",
            "🙂 Foto 2/3 — gira ligeramente la cabeza",
            "✨ Foto 3/3 — expresión natural"
        ]

        # =================================================
        # UI
        # =================================================
        self.title = QLabel("🧬 Registro de usuario")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del usuario")

        self.step_label = QLabel(self.steps_text[0])
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setObjectName("stepLabel")

        self.camera = QLabel()
        self.camera.setAlignment(Qt.AlignCenter)
        self.camera.setObjectName("camera")
        self.camera.setFixedSize(640, 480)

        self.progress = QProgressBar()
        self.progress.setMaximum(3)
        self.progress.setValue(0)

        self.btn_capture = QPushButton("📸 Capturar")
        self.btn_back = QPushButton("⬅ Volver")

        self.btn_capture.clicked.connect(self.capture)
        self.btn_back.clicked.connect(self.go_back)

        # =================================================
        # LAYOUT
        # =================================================
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        layout.addWidget(self.title)
        layout.addWidget(self.name_input)
        layout.addWidget(self.step_label)
        layout.addWidget(self.camera)
        layout.addWidget(self.progress)
        layout.addWidget(self.btn_capture)
        layout.addWidget(self.btn_back)

        self.setLayout(layout)

        # =================================================
        # TIMER
        # =================================================
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    # =====================================================
    # CAMERA LOOP (SHARED CAMERA)
    # =====================================================
    def update_frame(self):

        ok, frame = CameraManager.get().read()

        if not ok:
            return

        frame = cv2.flip(frame, 1)

        self.frame = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, _ = rgb.shape

        img = QImage(
            rgb.data,
            w,
            h,
            rgb.strides[0],
            QImage.Format_RGB888
        )

        pix = QPixmap.fromImage(img)

        pix = pix.scaled(
            self.camera.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        self.camera.setPixmap(pix)

    # =====================================================
    # CAPTURE STEP
    # =====================================================
    def capture(self):

        if self.frame is None:
            return

        name = self.name_input.text().strip()

        if not name:
            self.step_label.setText("⚠ Escribe un nombre válido")
            return

        # encode frame
        frame = cv2.resize(self.frame, (320, 240))

        _, buf = cv2.imencode(".jpg", frame)

        img_b64 = base64.b64encode(buf).decode()

        self.images.append(img_b64)

        self.step += 1
        self.progress.setValue(self.step)

        # =================================================
        # NEXT STEP OR FINISH
        # =================================================
        if self.step < 3:

            self.step_label.setText(
                self.steps_text[self.step]
            )

        else:

            self.step_label.setText("✨ Registrando usuario...")
            self.btn_capture.setEnabled(False)

            self.send(name)

    # =====================================================
    # SEND TO SERVER (THREAD)
    # =====================================================
    def send(self, name):

        url = (
            self.config.recognition_url()
            + "/register"
        )

        self.worker = RegisterWorker(
            url,
            name,
            self.images
        )

        self.worker.success.connect(
            self.on_success
        )

        self.worker.error.connect(
            self.on_error
        )

        self.worker.start()

    # =====================================================
    # SUCCESS
    # =====================================================
    def on_success(self):

        self.step_label.setText(
            "🌸 Usuario registrado con éxito"
        )

        QTimer.singleShot(1200, self.go_back)

    # =====================================================
    # ERROR
    # =====================================================
    def on_error(self, msg):

        self.step_label.setText(
            "⚠ Error en registro"
        )

        self.btn_capture.setEnabled(True)

    # =====================================================
    # BACK
    # =====================================================
    def go_back(self):

        self.timer.stop()

        self.images.clear()
        self.step = 0

        self.progress.setValue(0)

        self.btn_capture.setEnabled(True)

        self.controller.ui.show_login()

    # =====================================================
    # CLEAN EXIT
    # =====================================================
    def closeEvent(self, event):

        self.timer.stop()

        event.accept()           
            
            
