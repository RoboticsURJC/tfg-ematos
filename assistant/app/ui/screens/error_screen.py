from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

from app.core.logger import logger


class ErrorScreen(QWidget):

    def __init__(self, controller, message="Error"):
        super().__init__()

        logger.info(" -> Iniciando Error Screen")


        self.controller = controller

        layout = QVBoxLayout()

        label = QLabel("❌ Algo salió mal")
        label.setAlignment(Qt.AlignCenter)

        detail = QLabel(message)
        detail.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        layout.addWidget(detail)

        self.setLayout(layout)