from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

from app.core.logger import logger


class LauncherScreen(QWidget):

    open_app = pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller 
        
        logger.info(" -> Iniciando Launcher Screen")

        layout = QVBoxLayout()

        self.title = QLabel(f"🏠 Bienvenido")
        self.title.setAlignment(Qt.AlignCenter)

        info = QLabel("Selecciona una app")
        info.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title)
        layout.addWidget(info)

        self.setLayout(layout)
       
    def set_user(self, user):
        self.title.setText(f"Bienvenid@ {user}" )

