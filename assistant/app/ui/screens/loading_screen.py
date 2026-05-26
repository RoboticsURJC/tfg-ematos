from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer

from app.core.logger import logger


class LoadingScreen(QWidget):

    def __init__(self, text="Cargando..."):
        super().__init__()

        logger.info(" -> Iniciando Loading Screen")

        layout = QVBoxLayout()

        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)
        self.setLayout(layout)

        self.dots = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(400)

    def animate(self):
        self.dots = (self.dots + 1) % 4
        self.label.setText("Cargando" + "." * self.dots)