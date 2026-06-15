from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout
)

from app.ui.widgets.app_card import AppCard


class Dock(QWidget):

    def __init__(self, controller=None):
        super().__init__()

        self.controller = controller

        self.setFixedHeight(210)

        self.layout = QHBoxLayout()

        self.layout.setSpacing(18)

        self.layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        self.setLayout(self.layout)

    # =========================
    # ADD APP
    # =========================
    def add_app(self, app_name, icon="🧩"):

        card = AppCard(app_name, icon)

        card.clicked.connect(self.open_app)

        self.layout.addWidget(card)

    # =========================
    # OPEN APP
    # =========================
    def open_app(self, app_name):

        if self.controller:
            self.controller.open_app(app_name)
