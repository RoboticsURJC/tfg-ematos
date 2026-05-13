import sys
import os
import json
import base64
import cv2
import logging

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QDialog,
    QProgressBar
)

from PyQt5.QtCore import (
    QTimer,
    Qt,
    QThread,
    pyqtSignal
)

from PyQt5.QtGui import (
    QImage,
    QPixmap
)

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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("FaceClient")


# =========================
# WORKER API
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

            response = requests.post(
                f"{self.server_url}/recognize",
                json={"image": self.image},
                timeout=10
            )

            if response.ok:

                self.result_signal.emit(
                    response.json()
                )

            else:

                self.error_signal.emit(
                    f"Error servidor ({response.status_code})"
                )

        except Exception as e:

            self.error_signal.emit(
                f"Sin conexión: {e}"
            )


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

        # =========================
        # WINDOW
        # =========================
        self.setWindowTitle("Face Client")
        self.setFixedSize(640, 520)

        # =========================
        # DISPLAY SPI
        # =========================
        self.display = FaceDisplay(
            config_path=config_path
        )

        self.display.set_estado(
            "Sistema iniciado"
        )

        self.display.start()

        # =========================
        # CAMERA
        # =========================
        self.cap = cv2.VideoCapture(0)

        self.current_frame = None

        if not self.cap.isOpened():

            raise RuntimeError(
                "No se pudo abrir la cámara"
            )

        # =========================
        # UI
        # =========================
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)

        self.result_label = QLabel(
            "Esperando autenticación..."
        )

        self.result_label.setAlignment(
            Qt.AlignCenter
        )

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
        self.btn_login.clicked.connect(
            self.login
        )

        self.btn_register.clicked.connect(
            self.register
        )

        # =========================
        # CAMERA TIMER
        # =========================
        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_frame
        )

        self.timer.start(30)

    # =========================
    # CAMERA LOOP
    # =========================
    def update_frame(self):

        ret, frame = self.cap.read()

        if not ret:
            return

        # espejo
        frame = cv2.flip(frame, 1)

        self.current_frame = frame

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        h, w, ch = rgb.shape

        image = QImage(
            rgb.data,
            w,
            h,
            rgb.strides[0],
            QImage.Format_RGB888
        )

        self.image.setPixmap(
            QPixmap.fromImage(image).scaled(
                320,
                240,
                Qt.KeepAspectRatio
            )
        )

    # =========================
    # LOGIN
    # =========================
    def login(self):

        if self.current_frame is None:

            self.result_label.setText(
                "Cámara no lista"
            )

            return

        logger.info("Iniciando reconocimiento")

        self.display.set_estado(
            "Reconociendo rostro..."
        )

        self.popup = ProgressPopup(
            "Analizando rostro..."
        )

        self.popup.show()

        # reducir tamaño
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

    # =========================
    # RESULT
    # =========================
    def on_result(self, data):

        self.popup.close()

        names = data.get(
            "recognized",
            []
        )

        if names:

            user = names[0]

            logger.info(
                f"Usuario autenticado: {user}"
            )

            self.result_label.setText(
                f"Bienvenido {user}"
            )

            self.display.set_estado(
                f"Bienvenido {user}"
            )

            #  evento limpio
            self.on_authenticated(user)

        else:

            logger.warning(
                "Usuario no reconocido"
            )

            self.result_label.setText(
                "No reconocido"
            )

            self.display.set_estado(
                "Intruso detectado"
            )

    # =========================
    # ERROR
    # =========================
    def on_error(self, msg):

        logger.error(msg)

        self.popup.close()

        self.result_label.setText(msg)

        self.display.set_estado(
            "Error conexión"
        )

    # =========================
    # REGISTER
    # =========================
    def register(self):

        self.result_label.setText(
            "Registro no implementado"
        )

    # =========================
    # CLOSE
    # =========================
    def closeEvent(self, event):

        logger.info(
            "Cerrando FaceClient"
        )

        self.timer.stop()

        if self.cap:
            self.cap.release()

        self.display.stop()

        event.accept()


# =========================
# MAIN TEST
# =========================
if __name__ == "__main__":

    def fake_auth(user):
        print(f"AUTH OK -> {user}")

    app = QApplication(sys.argv)

    client = FaceClient(
        on_authenticated=fake_auth
    )

    client.show()

    sys.exit(app.exec_())