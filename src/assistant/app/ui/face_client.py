# app/ui/face_client.py

"""
@file face_client.py
@brief Cliente de reconocimiento facial y registro de usuarios.
@details Gestiona la captura de video vía OpenCV, el procesamiento asíncrono
mediante hilos (QThread) para la comunicación con el servidor de reconocimiento 
facial, y la actualización de la interfaz de usuario.
"""

import os
import json
import base64
import cv2
import requests

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QInputDialog,
    QProgressBar
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

from app.ui.display import FaceDisplay


# =========================================================
# CONFIG
# =========================================================

config_path = os.path.join(
    os.path.dirname(__file__),
    "../config/config.json"
)

with open(config_path, "r") as f:
    config = json.load(f)

SERVER_URL = config["server"]["recognition_url"]


# =========================================================
# THREAD LOGIN
# =========================================================

class Worker(QThread):
    """
    @brief Hilo secundario para realizar peticiones HTTP de reconocimiento facial.
    @details Evita el bloqueo del hilo principal de la UI al realizar operaciones
    de red (I/O) hacia el servidor de reconocimiento.
    
    @attr result_signal Señal que devuelve el JSON de respuesta del servidor.
    @attr error_signal Señal emitida en caso de fallo en la conexión o timeout.
    """

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

                self.result_signal.emit(
                    r.json()
                )

            else:

                self.error_signal.emit(
                    f"Servidor: {r.status_code}"
                )

        except Exception as e:

            self.error_signal.emit(str(e))


# =========================================================
# FACE CLIENT
# =========================================================

class FaceClient(QWidget):
    """
    @brief Interfaz principal de autenticación y registro facial.
    @details Coordina la visualización de la cámara, el control del display del 
    robot y la interacción con los servicios de reconocimiento facial del servidor.
    """

    def __init__(self, on_authenticated):
        
        """
        @brief Inicializa el cliente facial, la cámara y el display del robot.
        @param on_authenticated Callback que se ejecuta al reconocer exitosamente a un usuario.
        """
        
        super().__init__()

        self.on_authenticated = on_authenticated
        self.server_url = SERVER_URL

        # =====================================================
        # WINDOW
        # =====================================================

        self.setWindowTitle(
            "Asistente Facial"
        )

        self.setWindowFlags(
            Qt.Window
        )

        self.setAttribute(
            Qt.WA_StyledBackground,
            True
        )

        self.resize(1100, 760)

        # =====================================================
        # STATE
        # =====================================================

        self.logged_in = False

        # registro
        self.register_name = ""
        self.register_images = []

        # =====================================================
        # DISPLAY SPI
        # =====================================================

        self.display = FaceDisplay(
            config_path=config_path
        )

        self.display.set_estado(
            "Sistema iniciado"
        )

        self.display.start()

        # =====================================================
        # CAMERA
        # =====================================================

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():

            raise RuntimeError(
                "No se pudo abrir cámara"
            )

        self.current_frame = None

        # =====================================================
        # TITLE
        # =====================================================

        self.title = QLabel(
            " Asistente Facial"
        )

        self.title.setObjectName(
            "title"
        )

        self.title.setAlignment(
            Qt.AlignCenter
        )

        # =====================================================
        # CAMERA
        # =====================================================

        self.camera = QLabel()

        self.camera.setObjectName(
            "camera"
        )

        self.camera.setAlignment(
            Qt.AlignCenter
        )

        self.camera.setMinimumSize(
            960,
            540
        )

        # =====================================================
        # STATUS
        # =====================================================

        self.status = QLabel(
            " Esperando usuario..."
        )

        self.status.setObjectName(
            "status"
        )

        self.status.setAlignment(
            Qt.AlignCenter
        )

        # =====================================================
        # PROGRESS REGISTER
        # =====================================================

        self.progress = QProgressBar()

        self.progress.setMinimum(0)
        self.progress.setMaximum(5)

        self.progress.setValue(0)

        self.progress.hide()

        # =====================================================
        # BUTTONS
        # =====================================================

        self.btn_login = QPushButton(
            " Iniciar sesión"
        )

        self.btn_register = QPushButton(
            " Registrar usuario"
        )

        self.btn_capture = QPushButton(
            " Capturar foto"
        )

        self.btn_exit = QPushButton(
            " Salir"
        )

        self.btn_register.setObjectName(
            "secondary"
        )

        self.btn_exit.setObjectName(
            "exit"
        )

        self.btn_capture.hide()

        # =====================================================
        # BUTTON LAYOUT
        # =====================================================

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(14)

        buttons_layout.addWidget(
            self.btn_login
        )

        buttons_layout.addWidget(
            self.btn_register
        )

        buttons_layout.addWidget(
            self.btn_capture
        )

        buttons_layout.addWidget(
            self.btn_exit
        )

        # =====================================================
        # MAIN LAYOUT
        # =====================================================

        layout = QVBoxLayout()

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(18)

        layout.addWidget(
            self.title
        )

        layout.addWidget(
            self.camera,
            1
        )

        layout.addWidget(
            self.status
        )

        layout.addWidget(
            self.progress
        )

        layout.addLayout(
            buttons_layout
        )

        self.setLayout(layout)

        # =====================================================
        # EVENTS
        # =====================================================

        self.btn_login.clicked.connect(
            self.login
        )

        self.btn_register.clicked.connect(
            self.start_register
        )

        self.btn_capture.clicked.connect(
            self.capture_register_photo
        )

        self.btn_exit.clicked.connect(
            self.close_app
        )

        # =====================================================
        # TIMER CAMERA
        # =====================================================

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_frame
        )

        self.timer.start(30)

    # =====================================================
    # UPDATE CAMERA
    # =====================================================

    def update_frame(self):
        
        """
        @brief Slot del temporizador para actualizar el fotograma de la cámara.
        @details Convierte el frame de BGR (OpenCV) a RGB (Qt) y lo escala al widget.
        """

        ret, frame = self.cap.read()

        if not ret:
            return

        frame = cv2.flip(
            frame,
            1
        )

        self.current_frame = frame

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        h, w, _ = rgb.shape

        image = QImage(
            rgb.data,
            w,
            h,
            rgb.strides[0],
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(
            image
        )

        self.camera.setPixmap(
            pixmap.scaled(
                self.camera.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    # =====================================================
    # LOGIN
    # =====================================================

    def login(self):
        """
        @brief Captura la imagen actual e inicia el proceso de login en un hilo.
        """

        if self.current_frame is None:

            self.status.setText(
                "¡Cámara no lista!"
            )

            return

        self.status.setText(
            "Reconociendo rostro..."
        )

        self.display.set_estado(
            "Reconociendo rostro"
        )

        try:

            frame = cv2.resize(
                self.current_frame,
                (320, 240)
            )

            _, buffer = cv2.imencode(
                ".jpg",
                frame
            )

            img_b64 = base64.b64encode(
                buffer
            ).decode()

            self.worker = Worker(
                self.server_url,
                img_b64
            )

            self.worker.result_signal.connect(
                self.on_result
            )

            self.worker.error_signal.connect(
                self.on_error
            )

            self.worker.start()

        except Exception as e:

            print("LOGIN ERROR:", e)

            self.status.setText(
                " Error preparando imagen"
            )

    # =====================================================
    # LOGIN RESULT
    # =====================================================

    def on_result(self, data):
        """
        @brief Maneja la respuesta exitosa del servidor de reconocimiento.
        @param data Diccionario con la información del usuario reconocido.
        """

        print(
            "RESPUESTA SERVER:",
            data
        )

        names = data.get(
            "recognized",
            []
        )

        if len(names) > 0 and names[0] != "Desconocido":

            user = names[0]

            self.logged_in = True

            self.status.setText(
                f" Bienvenido {user}"
            )

            self.display.set_estado(
                f"Hola {user}"
            )

            self.on_authenticated(user)

            self.btn_login.hide()
            self.btn_register.hide()

        else:

            self.status.setText(
                " Rostro no reconocido"
            )

            self.display.set_estado(
                "Usuario no reconocido"
            )

    # =====================================================
    # ERROR
    # =====================================================

    def on_error(self, msg):

        print("ERROR:", msg)

        self.status.setText(
            "¡Sin conexión con servidor!"
        )

        self.display.set_estado(
            "Error conexión"
        )

    # =====================================================
    # START REGISTER
    # =====================================================

    def start_register(self):
        """@brief Inicia el flujo manual de captura para registrar un nuevo usuario."""

        name, ok = QInputDialog.getText(
            self,
            " Registro facial",
            "Nombre del usuario:"
        )

        if not ok or not name.strip():
            return

        self.register_name = name.strip()

        self.register_images = []

        self.progress.setValue(0)
        self.progress.show()

        self.btn_capture.show()

        self.status.setText(
            " Se tomarán 5 fotos manualmente"
        )

        self.display.set_estado(
            "Modo registro"
        )

        QMessageBox.information(
            self,
            "Registro facial",
            "Se tomarán 5 fotos.\n\n"
            "Pulsa 'Capturar foto' "
            "cada vez que estés listo "
        )

    # =====================================================
    # CAPTURE REGISTER PHOTO
    # =====================================================

    def capture_register_photo(self):
        """@brief Captura y guarda localmente una foto para el set de entrenamiento."""

        if self.current_frame is None:

            QMessageBox.warning(
                self,
                "Error",
                "Cámara no disponible"
            )

            return

        try:

            frame = cv2.resize(
                self.current_frame,
                (320, 240)
            )

            _, buffer = cv2.imencode(
                ".jpg",
                frame
            )

            img_b64 = base64.b64encode(
                buffer
            ).decode()

            self.register_images.append(
                img_b64
            )

            total = len(
                self.register_images
            )

            self.progress.setValue(
                total
            )

            self.status.setText(
                f"Foto {total}/5 capturada"
            )

            self.display.set_estado(
                f"Foto {total} capturada"
            )

            # =================================================
            # FINAL REGISTER
            # =================================================

            if total >= 5:

                self.finish_register()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    # =====================================================
    # FINISH REGISTER
    # =====================================================

    def finish_register(self):
        """@brief Envía el set de fotos capturadas al servidor para registrar el nuevo usuario."""

        try:

            self.status.setText(
                " Enviando registro..."
            )

            self.display.set_estado(
                "Procesando registro"
            )

            payload = {
                "name": self.register_name,
                "images": self.register_images
            }

            r = requests.post(
                f"{self.server_url}/register",
                json=payload,
                timeout=20
            )

            print(
                "REGISTER STATUS:",
                r.status_code
            )

            print(
                "REGISTER RESPONSE:",
                r.text
            )

            if r.ok:

                data = r.json()

                QMessageBox.information(
                    self,
                    " Registro completado",
                    data.get(
                        "message",
                        "Usuario registrado"
                    )
                )

                self.status.setText(
                    " Usuario registrado"
                )

                self.display.set_estado(
                    "Registro completado"
                )

            else:

                QMessageBox.warning(
                    self,
                    "Error servidor",
                    r.text
                )

                self.status.setText(
                    " Error en registro"
                )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

        finally:

            self.progress.hide()

            self.btn_capture.hide()

            self.register_images = []

    # =====================================================
    # CLOSE
    # =====================================================

    def close_app(self):
        """@brief Detiene los procesos de cámara, timers y cierra la aplicación."""

        self.timer.stop()

        if self.cap:
            self.cap.release()

        self.display.stop()

        self.close()

    # =====================================================
    # ESC CLOSE
    # =====================================================

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape:

            self.close_app()
