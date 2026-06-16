# app/ui/apps/boot/boot_screen.py

"""
@file boot_screen.py
@brief Pantalla de carga inicial (Splash Screen).
@details Gestiona la animación de inicio, aplica temas mediante QSS y coordina
la transición hacia el lanzador principal tras un tiempo de espera definido.
"""

import os
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStyleOption, QStyle
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QMovie, QFont, QPainter

from app.core.logger import logger


class BootScreen(QWidget):
    """
    @brief Pantalla de inicio de la aplicación.
    @details Hereda de QWidget y sobreescribe el ciclo de pintado para asegurar 
    que el fondo (degradado CSS) sea renderizado correctamente.
    """

    ## Señal emitida cuando finaliza el tiempo de carga
    finished = pyqtSignal()

    def __init__(self, controller):
        """
        @brief Inicializa la pantalla de carga.
        @param controller Objeto encargado de gestionar la navegación del sistema.
        """
        super().__init__()

        logger.info("[BOOT] BootScreen iniciado con fijación de pintura QSS")

        self.controller = controller
        self.setObjectName("bootScreen")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)

        # Configuración del componente de carga (GIF)
        self.loader = QLabel()
        self.loader.setAlignment(Qt.AlignCenter)
        self.loader.setStyleSheet("background: transparent;")

        self.movie = QMovie(self.get_loader_path())
        self.loader.setMovie(self.movie)
        self.movie.start()

        # Texto de estado
        self.label = QLabel("Iniciando Rojazz…")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setObjectName("bootText")
        self.label.setFont(QFont("Segoe UI", 32, QFont.Black))

        layout.addWidget(self.loader)
        layout.addWidget(self.label)

        self.setLayout(layout)

        # Aplicación de temas y temporizador de transición
        self.setStyleSheet(self.load_theme())
        QTimer.singleShot(3000, self.finish)

    def paintEvent(self, event):
        """
        @brief Sobreescritura necesaria para renderizar el fondo CSS en widgets personalizados.
        @details Utiliza QStyle para dibujar el primitivo de widget sobre el lienzo actual.
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

    def get_loader_path(self) -> str:
        """@brief Construye la ruta absoluta hacia el asset del cargador."""
        return os.path.join(
            os.path.dirname(__file__),
            "../themes/assets/loading.gif"
        )

    def load_theme(self) -> str:
        """@brief Define los estilos CSS para la pantalla de carga."""
        return """
        QWidget#bootScreen {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0.00 #f3ecff,
                stop: 0.50 #e8f4ff,
                stop: 1.00 #fff0f9
            );
        }

        QLabel#bootText {
            color: #583b76;
            background: transparent;
            font-weight: 900;
        }
        """

    def finish(self):
        """@brief Emite la señal 'finished' para avisar al controlador que puede continuar."""
        logger.info("[BOOT] Transición completada.")
        self.finished.emit()