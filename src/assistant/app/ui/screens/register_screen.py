# app/ui/screens/register_screen.py

"""
@file register_screen.py
@brief Pantalla de registro de nuevos usuarios mediante captura facial.
@details Gestiona la entrada de texto, la captura secuencial de tres imágenes 
para el entrenamiento del modelo, y la comunicación asíncrona con el servidor.
"""

import base64
import cv2
import requests

from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QProgressBar
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from app.core.camera_manager import CameraManager
from app.core.config import Config

from app.core.logger import logger



class RegisterWorker(QThread):
    """
    @brief Trabajador en segundo plano para el envío de datos de registro al servidor.
    """
    
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, name, images):
        super().__init__()
        self.url = url
        self.name = name
        self.images = images

    def run(self):
        """@brief Realiza la petición POST de registro de nuevo usuario."""
        try:
            r = requests.post(self.url, json={
                "name": self.name,
                "images": self.images
            }, timeout=15)

            if r.ok:
                self.success.emit()
            else:
                logger.info("[REGISTER] Error en server")
                self.error.emit("Server error")

        except Exception as e:
            self.error.emit(str(e))


class RegisterScreen(QWidget):
    
    """
    @brief Interfaz de usuario para el registro facial.
    @details Guía al usuario en un proceso de 3 pasos de captura de imagen.
    """

    def __init__(self, controller):
        
        """@brief Inicializa la UI de registro y los recursos de cámara."""
        
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)

        logger.info("[REGISTER] Iniciando ventana Register")
        self.setObjectName("registerScreen")
        self.controller = controller
        self.config = Config()
        self.setMinimumSize(950, 750)

        # ── REGISTER — Verde salvia / esmeralda pastel ────────────────────────
        self.setStyleSheet("""
        QWidget#registerScreen {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0.0 #f0faf4,
                stop:0.5 #d8f2e2,
                stop:1.0 #bfead0
            );
            font-family: "Segoe UI", "Ubuntu", sans-serif;
        }

        QLabel#title {
            font-size: 28px;
            font-weight: 900;
            color: #0d3d22;
            background: #a8e6be;
            border: 3px solid #4caa72;
            border-radius: 22px;
            padding: 14px 32px;
        }

        QLabel#stepLabel {
            background: #d8f2e2;
            border-radius: 20px;
            padding: 10px 20px;
            border: 3px solid #90d4aa;
            font-size: 18px;
            font-weight: 700;
            color: #1a5230;
        }

        QLabel#camera {
            border: 5px solid #5cc488;
            border-radius: 40px;
            background: #f0faf4;
        }

        QLineEdit {
            border-radius: 25px;
            padding: 12px 24px;
            border: 3px solid #5cc488;
            background: #f0faf4;
            font-size: 20px;
            font-weight: 600;
            color: #0d2e18;
            selection-background-color: #a8e6be;
            font-family: "Segoe UI", "Ubuntu", sans-serif;
        }
        QLineEdit:focus {
            border-color: #2e9958;
            background: white;
        }

        QPushButton {
            border-radius: 30px;
            padding: 14px 32px;
            font-weight: 900;
            font-size: 20px;
            font-family: "Segoe UI", "Ubuntu", sans-serif;
        }

        QPushButton#btn_capture {
            background-color: #4caa72;
            border: 4px solid #2e8050;
            color: white;
        }
        QPushButton#btn_capture:hover   { background-color: #389460; border-color: #1e6038; }
        QPushButton#btn_capture:pressed { background-color: #267a48; padding-top: 18px; }
        QPushButton#btn_capture:disabled {
            background-color: #bfead0;
            border-color: #90d4aa;
            color: #6a9e7e;
        }

        QPushButton#btn_back {
            background-color: #c0e8ce;
            border: 4px solid #6abf8a;
            color: #0d3d22;
        }
        QPushButton#btn_back:hover   { background-color: #a8e6be; border-color: #4caa72; }
        QPushButton#btn_back:pressed { background-color: #90d4aa; padding-top: 18px; }

        QProgressBar {
            border-radius: 10px;
            background: #bfead0;
            border: 2px solid #90d4aa;
            min-height: 18px;
            max-height: 18px;
            font-size: 0px;
        }
        QProgressBar::chunk {
            border-radius: 8px;
            background-color: #4caa72;
        }
        """)

        CameraManager.get().open()

        self.frame = None
        self.images = []
        self.step = 0

        self.title = QLabel("Registro Usuario")
        self.title.setObjectName("title")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre")

        self.step_label = QLabel("Paso 1")
        self.step_label.setObjectName("stepLabel")

        self.camera = QLabel()
        self.camera.setObjectName("camera")
        self.camera.setFixedSize(640, 480)

        self.progress = QProgressBar()
        self.progress.setMaximum(3)

        self.btn_capture = QPushButton(" Capturar")
        self.btn_capture.setObjectName("btn_capture")

        self.btn_back = QPushButton(" Volver")
        self.btn_back.setObjectName("btn_back")

        self.btn_capture.clicked.connect(self.capture)
        self.btn_back.clicked.connect(self.go_back)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.name_input)
        layout.addWidget(self.step_label)
        layout.addWidget(self.camera)
        layout.addWidget(self.progress)
        layout.addWidget(self.btn_capture)
        layout.addWidget(self.btn_back)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """@brief Actualiza la visualización de la cámara en tiempo real."""
        ok, frame = CameraManager.get().read()
        if not ok:
            return

        frame = cv2.flip(frame, 1)
        self.frame = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape

        img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)

        pix = pix.scaled(self.camera.size(), Qt.KeepAspectRatioByExpanding)
        self.camera.setPixmap(pix)

    def capture(self):
        """@brief Captura un frame actual y lo añade a la lista de entrenamiento."""
        if self.frame is None:
            return

        name = self.name_input.text().strip()
        if not name:
            self.step_label.setText("Escribe nombre")
            return

        frame = cv2.resize(self.frame, (320, 240))
        _, buf = cv2.imencode(".jpg", frame)
        self.images.append(base64.b64encode(buf).decode())

        self.step += 1
        self.progress.setValue(self.step)

        if self.step < 3:
            self.step_label.setText(f"Paso {self.step+1}")
        else:
            self.step_label.setText(" Registrando...")
            logger.info("[REGISTER] Registrando")
            self.btn_capture.setEnabled(False)
            self.send(name)

    def send(self, name):
        """@brief Inicia el trabajador de red para enviar las imágenes al servidor."""
        url = self.config.recognition_url() + "/register"

        self.worker = RegisterWorker(url, name, self.images)
        self.worker.success.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self):
        """@brief Maneja el éxito del registro."""
        logger.info("[REGISTER] Registro usuario correcto")
        self.step_label.setText(" listo")
        QTimer.singleShot(1000, self.go_back)

    def on_error(self, msg):
        """@brief Maneja el error del registro."""
        logger.info("[REGISTER] Error en registro")
        self.step_label.setText(" error")
        self.btn_capture.setEnabled(True)

    def go_back(self):
        """@brief Limpia el estado y regresa a la pantalla de login."""
        self.timer.stop()
        self.images.clear()
        self.step = 0
        self.progress.setValue(0)
        self.btn_capture.setEnabled(True)
        self.controller.ui.show_login()
