from datetime import datetime
import sys
import base64
import json
import requests
import os
import cv2
import logging

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QDialog, QLineEdit, QProgressBar,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QImage, QPixmap, QColor, QFont
from PyQt5.QtCore import (
    QTimer, Qt, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve
)

# ==================================================
# LOGGING
# ==================================================
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(
    LOG_DIR,
    f"client_{datetime.now().strftime('%Y-%m-%d')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("FaceClient")

# ==================================================
# CONFIG
# ==================================================
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

SERVER_URL = config["server_url"]
LLM_URL = config.get("llm_url", None)  #  FUTURO LLM

logger.info(f"Servidor: {SERVER_URL}")


# ==================================================
# UI MESSAGE
# ==================================================
def show_message(parent, mtype, title, text):
    logger.info(f"{mtype}: {title} - {text}")

    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)

    styles = {
        "info": {"icon": QMessageBox.Information, "color": "#78bbe7"},
        "warning": {"icon": QMessageBox.Warning, "color": "#e6c955"},
        "error": {"icon": QMessageBox.Critical, "color": "#ca4233"},
        "success": {"icon": QMessageBox.Information, "color": "#59f59a"},
    }

    style = styles.get(mtype, styles["info"])
    msg.setIcon(style["icon"])

    msg.setStyleSheet(f"""
        QMessageBox {{
            background-color: #2c3e50;
            color: white;
            font-size: 14px;
        }}
        QPushButton {{
            background-color: {style["color"]};
            border-radius: 8px;
            padding: 6px;
        }}
    """)

    msg.exec_()


# ==================================================
# THREAD RECONOCIMIENTO
# ==================================================
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
                self.error_signal.emit("Error servidor")

        except Exception as e:
            self.error_signal.emit(str(e))


# ==================================================
# POPUP PROGRESO
# ==================================================
class ProgressPopup(QDialog):
    def __init__(self, text="Procesando..."):
        super().__init__()

        self.setWindowTitle("Procesando")
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


# ==================================================
# REGISTRO
# ==================================================
class RegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Registro")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Nombre")

        self.btn = QPushButton("Registrar")
        self.btn.clicked.connect(self.accept_name)

        layout.addWidget(self.input)
        layout.addWidget(self.btn)

        self.setLayout(layout)

        self.name = None

    def accept_name(self):
        if self.input.text().strip():
            self.name = self.input.text().strip()
            self.accept()


# ==================================================
# APP PRINCIPAL
# ==================================================
class ClientApp(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Face AI Client")
        self.setFixedSize(640, 520)

        self.cap = cv2.VideoCapture(0)

        self.current_frame = None

        # ---------------- UI ----------------
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)

        self.result = QLabel("Esperando rostro...")
        self.result.setAlignment(Qt.AlignCenter)

        self.register_btn = QPushButton("Registrar usuario")

        layout = QVBoxLayout()
        layout.addWidget(self.image)
        layout.addWidget(self.register_btn)
        layout.addWidget(self.result)

        self.setLayout(layout)

        # eventos
        self.register_btn.clicked.connect(self.start_registration)

        # cámara loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # reconocimiento automático
        self.recognition_timer = QTimer()
        self.recognition_timer.timeout.connect(self.auto_recognize)
        self.recognition_timer.start(2000)

    # ==================================================
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        self.current_frame = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape

        img = QImage(rgb.data, w, h, QImage.Format_RGB888)
        self.image.setPixmap(QPixmap.fromImage(img))

    # ==================================================
    # RECONOCIMIENTO AUTOMÁTICO
    # ==================================================
    def auto_recognize(self):
        if self.current_frame is None:
            return

        frame = cv2.resize(self.current_frame, (320, 240))
        _, buffer = cv2.imencode(".jpg", frame)

        img = base64.b64encode(buffer).decode()

        self.worker = Worker(SERVER_URL, img)
        self.worker.result_signal.connect(self.on_result)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    # ==================================================
    def on_result(self, data):
        names = data.get("recognized", [])

        if not names:
            return

        if "Desconocido" in names:
            self.result.setText("🔒 Desconocido")
        else:
            name = ", ".join(names)
            self.result.setText(f"👋 Hola {name}")

            # 🔥 HOOK LLM FUTURO
            if LLM_URL:
                try:
                    requests.post(LLM_URL, json={"user": name})
                except:
                    pass

    def on_error(self, msg):
        self.result.setText("Error reconocimiento")

    # ==================================================
    # REGISTRO
    # ==================================================
    def start_registration(self):
        dialog = RegistrationDialog(self)

        if dialog.exec_() != QDialog.Accepted:
            return

        name = dialog.name

        images = []

        popup = ProgressPopup("Registrando...")
        popup.show()

        for _ in range(5):
            if self.current_frame is None:
                continue

            frame = cv2.imencode(".jpg", self.current_frame)[1]
            images.append(base64.b64encode(frame).decode())

            QTimer.singleShot(500, QApplication.processEvents)

        try:
            r = requests.post(
                f"{SERVER_URL}/register",
                json={"name": name, "images": images}
            )

            popup.close()

            if r.ok:
                show_message(self, "success", "OK", "Usuario registrado")
            else:
                show_message(self, "error", "Error", "Fallo registro")

        except Exception as e:
            popup.close()
            show_message(self, "error", "Error", str(e))


# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClientApp()
    window.show()
    sys.exit(app.exec_())