from PyQt5.QtWidgets import QLabel, QVBoxLayout, QPushButton
from app.ui.apps.base_app import BaseApp


class MusicApp(BaseApp):

    def __init__(self, controller=None, engine=None):
        super().__init__(controller, engine)

        self.app_name = "music"

        layout = QVBoxLayout()

        self.title = QLabel("🎵 Música")
        self.status = QLabel("Reproductor inactivo")

        self.btn_play = QPushButton("▶ Reproducir demo")
        self.btn_stop = QPushButton("⏹ Stop")

        self.btn_play.clicked.connect(self.play)
        self.btn_stop.clicked.connect(self.stop)

        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.btn_play)
        layout.addWidget(self.btn_stop)

        self.setLayout(layout)

    def play(self):
        self.status.setText("🎶 Reproduciendo... (simulado)")

        if self.engine:
            self.engine.display.set_estado("Música activa")

    def stop(self):
        self.status.setText("⏹ Detenido")

        if self.engine:
            self.engine.display.set_estado("Música detenida")
