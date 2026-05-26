from PyQt5.QtWidgets import QLabel, QVBoxLayout, QLineEdit, QPushButton
from app.ui.apps.base_app import BaseApp


class BrowserApp(BaseApp):

    def __init__(self, controller=None, engine=None):
        super().__init__(controller, engine)

        self.app_name = "browser"

        layout = QVBoxLayout()

        self.title = QLabel("🌐 Navegador IA")

        self.input = QLineEdit()
        self.input.setPlaceholderText("Pregunta algo o escribe una URL...")

        self.btn = QPushButton("Buscar")
        self.result = QLabel("")

        self.btn.clicked.connect(self.search)

        layout.addWidget(self.title)
        layout.addWidget(self.input)
        layout.addWidget(self.btn)
        layout.addWidget(self.result)

        self.setLayout(layout)

    def search(self):

        query = self.input.text()

        if not query:
            return

        if self.engine:
            try:
                res = self.engine.llm.ask(query)
                self.result.setText(res)
            except Exception:
                self.result.setText("⚠ Error")
