from PyQt5.QtWidgets import QLabel, QVBoxLayout, QPushButton
from app.ui.apps.base_app import BaseApp
import os
import psutil


class SystemApp(BaseApp):

    def __init__(self, controller=None, engine=None):
        super().__init__(controller, engine)

        self.app_name = "system"

        layout = QVBoxLayout()

        self.title = QLabel("⚙️ Sistema")

        self.info = QLabel("Listo")

        self.btn_refresh = QPushButton("Actualizar estado")
        self.btn_refresh.clicked.connect(self.update)

        self.btn_back = QPushButton("Volver")
        self.btn_back.clicked.connect(self.back)

        layout.addWidget(self.title)
        layout.addWidget(self.info)
        layout.addWidget(self.btn_refresh)
        layout.addWidget(self.btn_back)

        self.setLayout(layout)

    def update(self):

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        self.info.setText(
            f"CPU: {cpu}% | RAM: {ram}%"
        )

        if self.engine:
            self.engine.display.set_estado("Sistema monitorizado")
