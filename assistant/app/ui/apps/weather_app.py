from PyQt5.QtWidgets import QLabel, QVBoxLayout
from app.ui.apps.base_app import BaseApp


class WeatherApp(BaseApp):

    def __init__(self, controller=None, engine=None):
        super().__init__(controller, engine)

        self.app_name = "weather"

        layout = QVBoxLayout()

        self.title = QLabel("🌦️ Clima")
        self.info = QLabel("Consultando el clima del sistema...")

        layout.addWidget(self.title)
        layout.addWidget(self.info)

        self.setLayout(layout)

    def on_open(self):

        self.info.setText("🌍 Obteniendo datos...")

        if self.engine:
            try:
                weather = self.engine.llm.ask(
                    "Dame el clima actual en Madrid en 2 líneas"
                )
                self.info.setText(weather)
            except Exception:
                self.info.setText("⚠ No disponible")
