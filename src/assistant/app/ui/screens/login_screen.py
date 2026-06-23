# app/ui/screens/login_screen.py

"""
@file login_screen.py
@brief Pantalla de autenticación mediante reconocimiento facial.
@details Gestiona la captura de vídeo a través de CameraManager, el envío 
asíncrono de frames al motor de IA mediante trabajadores QThread y la 
transición de estado según el resultado de la autenticación.
"""

import base64
import cv2
import requests

from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from app.core.camera_manager import CameraManager
from app.core.config import Config
from app.core.logger import logger


class Worker(QThread):
    """
    @brief Trabajador en segundo plano para peticiones HTTP de reconocimiento facial.
    @details Evita que el hilo principal (UI) se bloquee durante la espera del servicio.
    """
    result_signal = pyqtSignal(dict)
    error_signal  = pyqtSignal(str)

    def __init__(self, url, image):
        super().__init__()
        self.url   = url
        self.image = image

    def run(self):
        """@brief Ejecuta la petición POST al servicio de reconocimiento."""
        try:
            response = requests.post(self.url, json={"image": self.image}, timeout=10)
            if response.ok:
                self.result_signal.emit(response.json())
            else:
                self.error_signal.emit(f"Error {response.status_code}")
        except Exception as e:
            self.error_signal.emit(str(e))


# ── LOGIN — Azul lavanda / índigo pastel ──────────────────────────────────────
STYLE = """
QWidget#loginScreen {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0.0 #f0f0ff,
        stop:0.5 #e0e4ff,
        stop:1.0 #cfd4ff
    );
}

QLabel#camera {
    border: 5px solid #8a9aff;
    border-radius: 36px;
    background: #f4f5ff;
}

QLabel#status {
    background: #e8ebff;
    border: 3px solid #b0baff;
    border-radius: 40px;
    padding: 14px 44px;
    font-size: 24px;
    font-weight: 800;
    color: #1a1f6e;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}

QLabel#userLabel {
    background: #b0baff;
    border: 3px solid #7a8aee;
    border-radius: 32px;
    padding: 12px 40px;
    font-size: 28px;
    font-weight: 900;
    color: #0d1150;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}

QPushButton#btn_login {
    background-color: #6b7ff0;
    border: 4px solid #4a5ce0;
    border-radius: 40px;
    padding: 20px 54px;
    font-size: 26px;
    font-weight: 900;
    color: white;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    min-height: 74px;
    min-width: 340px;
}
QPushButton#btn_login:hover   { background-color: #5568e8; border-color: #3348cc; }
QPushButton#btn_login:pressed { background-color: #3f52cc; padding-top: 24px; }

QPushButton#btn_register {
    background-color: #d0d6ff;
    border: 4px solid #8a96e8;
    border-radius: 40px;
    padding: 18px 50px;
    font-size: 24px;
    font-weight: 900;
    color: #1a1f6e;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    min-height: 70px;
    min-width: 340px;
}
QPushButton#btn_register:hover   { background-color: #b8c2ff; border-color: #6a78d8; }
QPushButton#btn_register:pressed { background-color: #a0aef8; padding-top: 22px; }
"""


class LoginScreen(QWidget):
    
    """
    @brief Interfaz de login.
    @details Muestra un stream de video en vivo, procesa el reconocimiento facial 
    y gestiona la navegación hacia el registro de usuarios.
    """

    def __init__(self, controller):
        
        """
        @brief Inicializa la pantalla, abre la cámara y configura el layout.
        @param controller Controlador principal para la gestión de estados.
        """
        
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        logger.info("[LOGIN] Iniciando ventana de Login")
        self.setObjectName("loginScreen")
        self.controller = controller
        self.config     = Config()
        self.setMinimumSize(900, 700)
        self.setStyleSheet(STYLE)

        CameraManager.get().open()
        self.current_frame = None

        self.camera = QLabel()
        self.camera.setObjectName("camera")
        self.camera.setAlignment(Qt.AlignCenter)
        self.camera.setFixedSize(640, 480)
         
        logger.info("[LOGIN] Esperando usuario")
        self.status = QLabel("  Esperando usuario...")
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignCenter)

        self.user_label = QLabel("")
        self.user_label.setObjectName("userLabel")
        self.user_label.setAlignment(Qt.AlignCenter)
        self.user_label.hide()

        self.btn_login    = QPushButton("  Iniciar sesión")
        self.btn_login.setObjectName("btn_login")
        self.btn_register = QPushButton("  Registrar usuario")
        self.btn_register.setObjectName("btn_register")

        self.btn_login.clicked.connect(self.login)
        self.btn_register.clicked.connect(self.go_register)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_login)
        btn_row.addWidget(self.btn_register)
        btn_row.addStretch()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(22)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addWidget(self.camera,     alignment=Qt.AlignCenter)
        layout.addWidget(self.status,     alignment=Qt.AlignCenter)
        layout.addWidget(self.user_label, alignment=Qt.AlignCenter)
        layout.addLayout(btn_row)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """@brief Lee el frame actual de la cámara y lo renderiza en la UI."""
        ok, frame = CameraManager.get().read()
        if not ok:
            return
        frame = cv2.flip(frame, 1)
        self.current_frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            self.camera.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.camera.setPixmap(pix)

    def login(self):
        """@brief Prepara la imagen actual y lanza el hilo de reconocimiento facial."""
        if self.current_frame is None:
            return
        self.status.setText("  Reconociendo...")
        logger.info("[LOGIN] Reconociendo ...")
        frame = cv2.resize(self.current_frame, (320, 240))
        _, buf  = cv2.imencode(".jpg", frame)
        img_b64 = base64.b64encode(buf).decode()
        self.worker = Worker(self.config.recognition_url() + "/recognize", img_b64)
        self.worker.result_signal.connect(self.on_result)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_result(self, data):
        """@brief Callback al recibir una respuesta exitosa del servidor."""
        names = data.get("recognized", [])
        if names and names[0] != "Desconocido":
            self.status.setText(" Usuario reconocido")
            logger.info("[LOGIN] Usuario reconocido")
            self.user_label.setText(f"¡Bienvenid@, {names[0]}!")
            self.user_label.show()
            self.timer.stop()
            self.controller.login(names[0])
        else:
            self.status.setText("  Usuario no reconocido")

    def on_error(self, msg):
        """@brief Lanzar error  al no recibir una respuesta exitosa del servidor."""
        logger.info("[LOGIN] Error de conexión")
        self.status.setText("  Error de conexión")


    def go_register(self):
        """@brief Llamar a la ventana de registro."""
        self.timer.stop()
        self.controller.ui.show_register()

    def showEvent(self, event):
        self.timer.start(30)
        super().showEvent(event)
