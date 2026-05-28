          
# app/ui/screens/login_screen.py

import os
import base64
import cv2
import requests

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout
)

from PyQt5.QtCore import (
    Qt,
    QTimer,
    QThread,
    pyqtSignal
)

from PyQt5.QtGui import (
    QImage,
    QPixmap
)

from app.core.camera_manager import CameraManager
from app.core.config import Config


# =====================================================
# WORKER
# =====================================================
class Worker(QThread):

    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, url, image):
        super().__init__()

        self.url = url
        self.image = image

    def run(self):

        try:

            response = requests.post(
                self.url,
                json={"image": self.image},
                timeout=10
            )

            if response.ok:
                self.result_signal.emit(response.json())

            else:
                self.error_signal.emit(
                    f"Error {response.status_code}"
                )

        except Exception as e:
            self.error_signal.emit(str(e))


# =====================================================
# LOGIN SCREEN
# =====================================================
class LoginScreen(QWidget):

    def __init__(self, controller):

        super().__init__()

        self.controller = controller
        self.config = Config()

        self.setObjectName("loginScreen")
        self.setMinimumSize(900, 700)

        # =================================================
        # QSS
        # =================================================
        qss_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "themes",
            "login.qss"
        )

        qss_path = os.path.abspath(qss_path)

        if os.path.exists(qss_path):

            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        # =================================================
        # CAMERA SHARED
        # =================================================
        CameraManager.get().open()

        self.current_frame = None

        # =================================================
        # UI
        # =================================================
        self.camera = QLabel()
        self.camera.setAlignment(Qt.AlignCenter)
        self.camera.setObjectName("camera")
        self.camera.setFixedSize(640, 480)

        self.status = QLabel("Esperando usuario...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setObjectName("status")

        self.user_label = QLabel("")
        self.user_label.setAlignment(Qt.AlignCenter)
        self.user_label.setObjectName("userLabel")

        self.btn_login = QPushButton("✨ Iniciar sesión")

        self.btn_register = QPushButton(
            "🧬 Registrar usuario"
        )

        self.btn_login.clicked.connect(self.login)

        self.btn_register.clicked.connect(
            self.go_register
        )

        # =================================================
        # LAYOUT
        # =================================================
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        layout.addWidget(self.camera)
        layout.addWidget(self.status)
        layout.addWidget(self.user_label)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_register)

        self.setLayout(layout)

        # =================================================
        # TIMER
        # =================================================
        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_frame
        )

        self.timer.start(30)

    # =====================================================
    # CAMERA LOOP
    # =====================================================
    def update_frame(self):

        ok, frame = CameraManager.get().read()

        if not ok:
            return

        frame = cv2.flip(frame, 1)

        self.current_frame = frame

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

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
    # LOGIN
    # =====================================================
    def login(self):

        if self.current_frame is None:
            return

        self.status.setText("🔍 Reconociendo...")

        frame = cv2.resize(
            self.current_frame,
            (320, 240)
        )

        _, buf = cv2.imencode(".jpg", frame)

        img_b64 = base64.b64encode(buf).decode()

        url = (
            self.config.recognition_url()
            + "/recognize"
        )

        self.worker = Worker(url, img_b64)

        self.worker.result_signal.connect(
            self.on_result
        )

        self.worker.error_signal.connect(
            self.on_error
        )

        self.worker.start()

    # =====================================================
    # RESULT
    # =====================================================
    def on_result(self, data):

        names = data.get("recognized", [])

        if names and names[0] != "Desconocido":

            user = names[0]

            self.status.setText(
                "✨ Usuario reconocido"
            )

            self.user_label.setText(
                f"Bienvenido {user}"
            )
            
            print(user)
            
            self.timer.stop()
            
            self.controller.login(user)

        else:

            self.status.setText(
                "❌ Usuario no reconocido"
            )

    # =====================================================
    # ERROR
    # =====================================================
    def on_error(self, msg):

        self.status.setText(
            "⚠ Error de conexión"
        )

    # =====================================================
    # GO REGISTER
    # =====================================================
    def go_register(self):

        self.timer.stop()

        self.controller.ui.show_register()

    # =====================================================
    # SHOW EVENT
    # =====================================================
    def showEvent(self, event):

        self.timer.start(30)

        super().showEvent(event) 
        
        
