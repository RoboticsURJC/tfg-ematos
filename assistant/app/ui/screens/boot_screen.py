import os

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QMovie, QPalette, QColor

from app.core.logger import logger


class BootScreen(QWidget):

    finished = pyqtSignal()

    def __init__(self, controller):
        super().__init__()

        logger.info("BootScreen iniciado")

        self.controller = controller

        # =========================
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#1a1b2e"))
        self.setPalette(palette)

        self.setObjectName("bootScreen")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # =========================
        # GIF
        # =========================
        self.loader = QLabel()
        self.loader.setAlignment(Qt.AlignCenter)

        self.movie = QMovie(self.get_loader_path())
        self.loader.setMovie(self.movie)
        self.movie.start()

        # =========================
        # TEXT
        # =========================
        self.label = QLabel("Iniciando Rojazz…")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setObjectName("bootText")

        layout.addWidget(self.loader)
        layout.addWidget(self.label)

        self.setLayout(layout)

        # =========================
        # STYLE (solo texto)
        # =========================
        self.setStyleSheet(self.load_theme())

        # =========================
        # TIMER
        # =========================
        QTimer.singleShot(3000, self.finish)

    def get_loader_path(self):

        return os.path.join(
            os.path.dirname(__file__),
            "../themes/assets/loading.gif"
        )

    def load_theme(self):

        return """
        QWidget#bootScreen {
            background: transparent;
        }

        QLabel#bootText {
            color: black;
            font-size: 28px;
            font-weight: 600;
        }
        """

    def finish(self):
        self.finished.emit()
