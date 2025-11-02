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
    QMessageBox, QDialog, QLineEdit, QProgressBar, 
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QImage, QPixmap, QColor, QFont
from PyQt5.QtCore import (
    QTimer, Qt, QThread, pyqtSignal, QPropertyAnimation, 
    QEasingCurve, QRect)


# ----- Cargar configuración -----
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

SERVER_URL = config["server_url"]


def show_message(parent, mtype, title, text):
    """
    Muestra un QMessageBox personalizado según el tipo.
    Tipos válidos: info, warning, error, success.
    """
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)

    # ---- Configurar según tipo ----
    styles = {
        "info":    {"icon": QMessageBox.Information, "color": "#3498db"},
        "warning": {"icon": QMessageBox.Warning,     "color": "#f1c40f"},
        "error":   {"icon": QMessageBox.Critical,    "color": "#ca4233"},
        "success": {"icon": QMessageBox.Information, "color": "#2ecc71"},
    }

    style = styles.get(mtype, styles["info"])
    msg.setIcon(style["icon"])

    # ---- Estilo visual (tema oscuro elegante) ----
    msg.setStyleSheet(f"""
        QMessageBox {{
            background-color: #2c3e50;
            color: white;
            font-family: 'Segoe UI';
            font-size: 14px;
            border-radius: 12px;
            padding: 10px;
        }}
        QMessageBox QLabel {{
            color: #ecf0f1;
            font-weight: bold;
        }}
        QPushButton {{
            background-color: {style["color"]};
            color: white;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {QColor(style["color"]).lighter(120).name()};
        }}
        QPushButton:pressed {{
            background-color: {QColor(style["color"]).darker(150).name()};
        }}
    """)

    msg.exec_()


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
        self.setFixedSize(420, 230)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        # Fondo con degradado suave
        self.setStyleSheet("""
        QDialog {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #1f2c3a,
                stop:1 #34495e
            );
            border-radius: 14px;
        }

        QLabel {
            color: #ecf0f1;
            font-family: 'Segoe UI', Arial;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            padding: 4px;
        }

        QLineEdit {
            background-color: rgba(255, 255, 255, 0.15);
            color: #ecf0f1;
            border: 2px solid #2980b9;
            border-radius: 8px;
            padding: 8px;
            font-size: 15px;
            selection-background-color: #3498db;
        }

        QLineEdit:focus {
            border: 2px solid #1abc9c;
            background-color: rgba(255, 255, 255, 0.25);
        }

        QPushButton {
            background-color: #27ae60;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-weight: bold;
            font-size: 15px;
        }

        QPushButton:hover {
            background-color: #2ecc71;
        }

        QPushButton:pressed {
            background-color: #1e8449;
        }
        """)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        # Título
        title_label = QLabel("Registro de nuevo usuario")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 17, QFont.Bold))
        layout.addWidget(title_label)

        # Campo de nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Introduce el nombre del usuario")
        layout.addWidget(self.name_input)

        # Botón de registrar
        self.register_btn = QPushButton("Registrar")
        layout.addWidget(self.register_btn)

        # Sombra sutil al botón
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 3)
        self.register_btn.setGraphicsEffect(shadow)

        self.setLayout(layout)
        self.registered_name = None
        self.register_btn.clicked.connect(self.try_register)

    def try_register(self):
        name = self.name_input.text().strip()
        if not name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Por favor, introduce un nombre válido.")
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
                # QMessageBox.warning(self, "Inicio fallido", "Usuario desconocido.")
                show_message(self, "warning", "Inicio fallido", "Usuario desconocido." )
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
        
    def add_hover_animation(self, button):
        """Agrega una animación sutil de agrandamiento al pasar el mouse."""
        base_rect = None

        def on_enter(event):
            nonlocal base_rect
            base_rect = button.geometry()
            anim = QPropertyAnimation(button, b"geometry")
            anim.setDuration(120)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            anim.setStartValue(button.geometry())
            anim.setEndValue(base_rect.adjusted(-3, -3, 3, 3))
            anim.start()
            button._anim = anim  # guardar referencia para evitar GC

        def on_leave(event):
            if base_rect:
                anim = QPropertyAnimation(button, b"geometry")
                anim.setDuration(120)
                anim.setEasingCurve(QEasingCurve.InOutQuad)
                anim.setStartValue(button.geometry())
                anim.setEndValue(base_rect)
                anim.start()
                button._anim = anim

        button.enterEvent = on_enter
        button.leaveEvent = on_leave
    
    def start_registration(self):
        dialog = RegistrationDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        name = dialog.registered_name

        # --- Ventana emergente de registro ---
        capture_popup = QDialog(self)
        capture_popup.setWindowTitle("Registro de Usuario")
        capture_popup.setFixedSize(420, 250)
        capture_popup.setModal(True)
        capture_popup.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        )

        capture_popup.setStyleSheet("""
            QDialog {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e2a38,
                    stop:1 #2c3e50
                );
                border-radius: 15px;
            }

            QLabel {
                color: #ecf0f1;
                font-family: 'Segoe UI', Arial;
                font-size: 15px;
                font-weight: bold;
                padding: 6px;
                text-align: center;
            }

            QProgressBar {
                border: 2px solid #27ae60;
                border-radius: 8px;
                text-align: center;
                color: #ecf0f1;
                font-weight: bold;
                height: 18px;
                background-color: rgba(255,255,255,0.1);
            }

            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 6px;
            }

            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                margin: 4px 12px;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QPushButton:pressed {
                background-color: #1f618d;
            }

            QPushButton#cancel {
                background-color: #e74c3c;
            }

            QPushButton#cancel:hover {
                background-color: #c0392b;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        label = QLabel("Prepárate para la primera foto")
        label.setAlignment(Qt.AlignCenter)

        progress = QProgressBar()
        progress.setMaximum(5)
        progress.setValue(0)

        take_btn = QPushButton("Hacer foto")
        cancel_btn = QPushButton("Cancelar registro")
        cancel_btn.setObjectName("cancel")

        # 💫 Añadimos animaciones de hover reales
        self.add_hover_animation(take_btn)
        self.add_hover_animation(cancel_btn)

        layout.addWidget(label)
        layout.addWidget(progress)
        layout.addWidget(take_btn)
        layout.addWidget(cancel_btn)
        capture_popup.setLayout(layout)
        
        # 🔹 Calcular posición del popup al lado derecho de la ventana principal
        main_geo = self.geometry()
        popup_x = main_geo.x() + main_geo.width() + 20
        popup_y = main_geo.y() + 80

        # 🔹 Evitar que se salga de la pantalla (por si el usuario tiene monitor pequeño)
        screen = QApplication.primaryScreen().availableGeometry()
        if popup_x + capture_popup.width() > screen.width():
            popup_x = main_geo.x() - capture_popup.width() - 20  # Mover a la izquierda si no cabe

        capture_popup.move(popup_x, popup_y)


        capture_popup.show()

        images = []
        cancelled = {"state": False}
        
        def cancel_process():
            cancelled["state"] = True
            capture_popup.close()
            show_message(self, "info", "Registro cancelado", "El registro fue cancelado por el usuario.")
           
        cancel_btn.clicked.connect(cancel_process)
        
        def take_photo():
            if cancelled["state"]:
                capture_popup.close()
                return

            current_photo = len(images) + 1

            label.setText(f"Preparando para capturar foto {current_photo}/5...")
            QApplication.processEvents()
            QTimer.singleShot(800, lambda: capture(current_photo))

        def capture(current_photo):
            if self.current_frame is not None:
                _, buffer = cv2.imencode(".jpg", self.current_frame)
                img_str = base64.b64encode(buffer).decode("utf-8")
                images.append(img_str)
                progress.setValue(current_photo)
                label.setText(f"Foto {current_photo} capturada correctamente.")
            else:
                # QMessageBox.critical(self, "Error", "No se pudo capturar la imagen.")
                show_message(self, "error", "Error", "No se pudo capturar la imagen.")
                capture_popup.close()
                return

            if current_photo < 5:
                next_photo = current_photo + 1
                take_btn.setText(f"Tomar foto {next_photo}/5")
                label.setText(f"Prepárate para la foto {next_photo}/5")
            else:
                take_btn.setEnabled(False)
                label.setText("Subiendo imágenes al servidor...")
                QApplication.processEvents()

                try:
                    response = requests.post(
                        f"{SERVER_URL}/register",
                        json={"name": name, "images": images},
                        timeout=15
                    )
                    capture_popup.close()
                    data = response.json() if response.ok else {}

                    if response.ok and data.get("status") == "ok":
                        show_message(self, "success", "Registro exitoso", f"Usuario {name} registrado con éxito")
                        # QMessageBox.information(
                        #     self, "Registro exitoso", f"Usuario {name} registrado con éxito"
                        # )
                        

                    else:
                        msg = data.get("message", "Error desconocido al registrar el usuario.")
                        # QMessageBox.warning(self, "Error en registro", msg)
                        show_message(self, "warning","Error en registro", msg)

                except requests.exceptions.RequestException:
                    capture_popup.close()
                    # QMessageBox.critical(
                    #     self, "Error de conexión", "No se pudo conectar al servidor."
                    # )
                    show_message(self, "error", "Error de conexión", "No se pudo conectar al servidor.")


        take_btn.clicked.connect(take_photo)


# ----- Ejecutar aplicación -----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ClientApp()
    client.show()
    sys.exit(app.exec_())
