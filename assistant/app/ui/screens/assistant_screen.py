from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from app.core.logger import logger

class AssistantScreen(QWidget):

    def __init__(self, engine):
        super().__init__()

        logger.info(" -> Iniciando Assistant Screen")

        self.engine = engine

        layout = QVBoxLayout()

        self.title = QLabel("🤖 Asistente activo")
        self.title.setAlignment(Qt.AlignCenter)

        self.state = QLabel("Esperando orden...")
        self.state.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title)
        layout.addWidget(self.state)

        self.setLayout(layout)

    def set_state(self, text):
        self.state.setText(text)