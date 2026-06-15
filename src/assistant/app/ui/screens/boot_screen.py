import os

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStyleOption, QStyle
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QMovie, QFont, QPainter

from app.core.logger import logger


class BootScreen(QWidget):

    finished = pyqtSignal()

    def __init__(self, controller):
        super().__init__()

        logger.info("[BOOT] BootScreen iniciado con fijación de pintura QSS")

        self.controller = controller

        # Nombre de objeto para el QSS
        self.setObjectName("bootScreen")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)

        # =========================
        # GIF
        # =========================
        self.loader = QLabel()
        self.loader.setAlignment(Qt.AlignCenter)
        self.loader.setStyleSheet("background: transparent;")

        self.movie = QMovie(self.get_loader_path())
        self.loader.setMovie(self.movie)
        self.movie.start()

        # =========================
        # TEXTO DE CARGA
        # =========================
        self.label = QLabel("Iniciando Rojazz…")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setObjectName("bootText")
        self.label.setFont(QFont("Segoe UI", 32, QFont.Black))

        layout.addWidget(self.loader)
        layout.addWidget(self.label)

        self.setLayout(layout)

        # Aplicar el estilo con el degradado
        self.setStyleSheet(self.load_theme())

        # TIMER
        QTimer.singleShot(3000, self.finish)

    def paintEvent(self, event):
        """
        ESTA ES LA MAGIA: Obliga a las subclases de QWidget 
        a respetar y dibujar los fondos declarados en el QSS.
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

    def get_loader_path(self):
        return os.path.join(
            os.path.dirname(__file__),
            "../themes/assets/loading.gif"
        )

    def load_theme(self):
        return """
        QWidget#bootScreen {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0.00 #f3ecff,  /* Morado dulce */
                stop: 0.50 #e8f4ff,  /* Azul cielo */
                stop: 1.00 #fff0f9   /* Rosa suave */
            );
        }

        QLabel#bootText {
            color: #583b76;
            background: transparent;
            font-weight: 900;
        }
        """

    def finish(self):
        self.finished.emit()
