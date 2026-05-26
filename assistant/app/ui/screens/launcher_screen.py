from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

from app.core.logger import logger


class LauncherScreen(QWidget):

    open_app = pyqtSignal(str)

    def __init__(self, user=""):
        super().__init__()

        logger.info(" -> Iniciando Launcher Screen")

        layout = QVBoxLayout()

        title = QLabel(f"🏠 Bienvenido {user}")
        title.setAlignment(Qt.AlignCenter)

        info = QLabel("Selecciona una app")
        info.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(info)

        self.setLayout(layout)