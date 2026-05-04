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
# LOGGING CONFIG
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

# ----- Cargar configuración -----
## @brief Cargar configuración desde archivo JSON
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

## @brief URL del servidor backend
SERVER_URL = config["server_url"]
logger.info(f"Servidor configurado en: {SERVER_URL}")



# --------------------------------------------------
# MENSAJES UI
# --------------------------------------------------
def show_message(parent, mtype, title, text):
    """
    @brief Muestra un mensaje personalizado.

    @param parent Widget padre
    @param mtype Tipo: info, warning, error, success
    @param title Título
    @param text Contenido
    """
    
    logger.info(f"UI MESSAGE -> {mtype}: {title} - {text}")

    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)

    # ---- Configurar según tipo ----
    styles = {
        "info":    {"icon": QMessageBox.Information, "color": "#78bbe7"},
        "warning": {"icon": QMessageBox.Warning,     "color": "#e6c955"},
        "error":   {"icon": QMessageBox.Critical,    "color": "#ca4233"},
        "success": {"icon": QMessageBox.Information, "color": "#59f59a"},
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
    """
    @brief Hilo para enviar imágenes al servidor sin bloquear la UI.
    """
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, server_url, image_b64):
        super().__init__()
        self.server_url = server_url
        self.image_b64 = image_b64

    def run(self):
        """@brief Ejecuta la petición HTTP."""
        try:

            logger.info("Enviando imagen al servidor (recognize)...")

            response = requests.post(
                f"{self.server_url}/recognize",
                json={"image": self.image_b64},
                timeout=5
            )
            if response.ok:
                logger.info("Respuesta recibida correctamente")
                self.result_signal.emit(response.json())
            else:
                logger.error(f"Error servidor: {response.status_code}")
                self.error_signal.emit("Error del servidor")
                
        except Exception as e:
            logger.error(f"Fallo conexión: {e}")
            self.error_signal.emit("No se pudo conectar al servidor")



# --------------------------------------------------
# POPUP PROGRESO
# --------------------------------------------------

class ProgressPopup(QDialog):
    """
    @brief Ventana de carga mientras se procesa la imagen.
    """
    def __init__(self, message="Procesando..."):
        super().__init__()
        
        logger.info("Mostrando popup de progreso")

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
    """
    @brief Diálogo para introducir el nombre del usuario.
    """
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
        """@brief Valida el nombre introducido."""

        name = self.name_input.text().strip()
        if not name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Por favor, introduce un nombre válido.")
            return
        self.registered_name = name
        self.accept()


# --------------------------------------------------
# APP PRINCIPAL
# --------------------------------------------------
class ClientApp(QWidget):
    """
    @brief Aplicación principal de reconocimiento facial.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Client")
        self.setFixedSize(640, 520)
        self.setStyleSheet("background-color: #2c3e50;")

        logger.info("Inicializando aplicación...")

        # -------- Cámara USB --------
        ## @brief Inicializa cámara con OpenCV
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        
        if not self.cap.isOpened():
            logger.error("No se pudo abrir la cámara USB")
            raise RuntimeError("No se pudo abrir la cámara USB")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        logger.info("Cámara USB inicializada correctamente")

        self.current_frame = None

        # -------- UI --------
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
            QPushButton:focus {
                outline: none;
                border: none;
            }

            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """
        
        # -------- Eventos --------
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

        # -------- Timer --------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """
        @brief Captura y muestra un frame de la cámara USB.
        """
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Frame no recibido de cámara")
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.flip(rgb, 1)

        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(img).scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(pixmap)

        ## Guardamos frame original para enviar
        self.current_frame = frame


    # ---------------- LOGIN ----------------

    def capture_and_send(self):
        """
        @brief Captura frame actual y lo envía al servidor.
        """
        
        logger.info("Captura para login iniciada")

        if self.current_frame is None:
            logger.warning("Cámara no lista")
            self.result_label.setText("Cámara no lista")
            return

        popup = ProgressPopup("Login...")
        popup.show()
        
        self.progress_popup = ProgressPopup("Iniciando sesión...")
        self.progress_popup.show()

        frame_resized = cv2.resize(self.current_frame, (320, 240))
        _, buffer = cv2.imencode(".jpg", frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
        img_str = base64.b64encode(buffer).decode("utf-8")

        self.worker = Worker(SERVER_URL, img_str)
        self.worker.result_signal.connect(self.on_recognition_result)
        self.worker.error_signal.connect(self.on_recognition_error)
        self.worker.start()

    def iniciar_asistente(self, usuario):
        """Lanza el proceso del asistente con el usuario reconocido."""
        import subprocess
        subprocess.Popen(["python3", "asistente_robotico.py", usuario])
        
    def on_recognition_result(self, data):
        """@brief Maneja respuesta del servidor."""

        self.progress_popup.close()
        logger.info(f"Resultado: {data}")

        names = data.get("recognized", [])
        if names and  "Desconocido" not in names:
            usuario = names[0]
            self.result_label.setText(f"Bienvenid@ {', '.join(names)}!")
            
            self.iniciar_asistente(usuario)
        else:
            show_message(self, "warning", "Inicio fallido", "Usuario desconocido.")
        self.result_label.setStyleSheet("color: white; font-weight: bold")

    def on_recognition_error(self, message):
        """@brief Maneja errores."""
        logger.error(f"Error reconocimiento: {message}")

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
    
    
    # ---------------- REGISTRO ----------------
    
    def start_registration(self):
        """
        @brief Flujo completo de registro de usuario mediante captura de imágenes desde cámara USB.

        Este método:
        - Solicita el nombre del usuario.
        - Abre un popup interactivo.
        - Captura 5 imágenes desde la cámara USB.
        - Envía las imágenes al servidor para registrar el rostro.

        @note Usa self.current_frame actualizado desde OpenCV (VideoCapture).
        """
        
        logger.info("Inicio de registro de usuario")

        
        # ---------------------------
        # 1. Pedir nombre de usuario
        # ---------------------------
        dialog = RegistrationDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        name = dialog.registered_name

        # ---------------------------
        # 2. Crear ventana de captura
        # ---------------------------
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

        # Añadimos animaciones de hover reales
        self.add_hover_animation(take_btn)
        self.add_hover_animation(cancel_btn)

        layout.addWidget(label)
        layout.addWidget(progress)
        layout.addWidget(take_btn)
        layout.addWidget(cancel_btn)
        capture_popup.setLayout(layout)
        
        # Calcular posición del popup al lado derecho de la ventana principal
        main_geo = self.geometry()
        popup_x = main_geo.x() + main_geo.width() + 20
        popup_y = main_geo.y() + 80

        # Evitar que se salga de la pantalla (por si el usuario tiene monitor pequeño)
        screen = QApplication.primaryScreen().availableGeometry()
        if popup_x + capture_popup.width() > screen.width():
            popup_x = main_geo.x() - capture_popup.width() - 20  # Mover a la izquierda si no cabe

        capture_popup.move(popup_x, popup_y)


        capture_popup.show()
        
        # ---------------------------
        # 3. Variables de control
        # ---------------------------
        images = []
        cancelled = {"state": False}
        
        
        # ---------------------------
        # 4. Cancelar proceso
        # ---------------------------
        def cancel_process():
            """
            @brief Cancela el registro en curso.
            """
            cancelled["state"] = True
            capture_popup.close()
            show_message(self, "info", "Registro cancelado", "El registro fue cancelado por el usuario.")
           
        cancel_btn.clicked.connect(cancel_process)
        
        
        # ---------------------------
        # 5. Botón tomar foto
        # ---------------------------
        def take_photo():
            """
            @brief Prepara la captura con pequeño delay para UX.
            """
            
            logger.info("Preparando camara para tomar foto")

            
            if cancelled["state"]:
                capture_popup.close()
                return

            current_photo = len(images) + 1

            label.setText(f"Preparando para capturar foto {current_photo}/5...")
            QApplication.processEvents()
            
            # Delay para dar tiempo al usuario a colocarse
            QTimer.singleShot(800, lambda: capture(current_photo))

        
        # ---------------------------
        # 6. Captura de imagen
        # ---------------------------
        def capture(current_photo):
            """
            @brief Captura una imagen desde la cámara USB.

            @param current_photo Número de foto actual.
            """
            
            logger.info("Capturando imagen")

        
            if self.current_frame is not None:
                _, buffer = cv2.imencode(".jpg", self.current_frame)
                img_str = base64.b64encode(buffer).decode("utf-8")
                images.append(img_str)
                progress.setValue(current_photo)
                label.setText(f"Foto {current_photo} capturada correctamente.")
            else:
                # QMessageBox.critical(self, "Error", "No se pudo capturar la imagen.")
                show_message(self, "error", "Error", "No se pudo capturar la imagen.")
                logger.error("No se pudo capturar la imagen.")

                capture_popup.close()
                return

            # ---------------------------
            # 7. Siguiente foto o envío
            # ---------------------------
            if current_photo < 5:
                next_photo = current_photo + 1
                take_btn.setText(f"Tomar foto {next_photo}/5")
                logger.info(f"Tomar foto {next_photo}/5")
                label.setText(f"Prepárate para la foto {next_photo}/5")
            else:
                take_btn.setEnabled(False)
                logger.info("Subiendo imágenes al servidor...")
                label.setText("Subiendo imágenes al servidor...")
                QApplication.processEvents()
                
                # ---------------------------
                # 8. Enviar al servidor
                # ---------------------------
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
                        logger.info(f"Registro exitoso", f"Usuario {name} registrado con éxito")

                    else:
                        msg = data.get("message", "Error desconocido al registrar el usuario.")
                        logger.warning("Error desconocido al registrar el usuario.")
                        show_message(self, "warning","Error en registro", msg)

                except requests.exceptions.RequestException:
                    capture_popup.close()
                    show_message(self, "error", "Error de conexión", "No se pudo conectar al servidor.")
                    logger.error("Error de conexión, no se pudo conectar al servidor. ")


        take_btn.clicked.connect(take_photo)


# ----- Ejecutar aplicación -----
if __name__ == "__main__":
    
    logger.info(f"Iniciando API....")

    app = QApplication(sys.argv)
    client = ClientApp()
    client.show()
    sys.exit(app.exec_())