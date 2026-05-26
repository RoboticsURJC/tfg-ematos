from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout
)

from PyQt5.QtCore import Qt


class StatusBar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(38)

        self.setObjectName("statusBar")

        # =========================
        # LABELS
        # =========================
        self.status = QLabel("🟢 Sistema listo")

        self.user = QLabel("Invitado")

        # =========================
        # LAYOUT
        # =========================
        layout = QHBoxLayout()

        layout.setContentsMargins(12, 4, 12, 4)

        layout.addWidget(self.status)

        layout.addStretch()

        layout.addWidget(self.user)

        self.setLayout(layout)

        # =========================
        # STYLE
        # =========================
        self.setStyleSheet("""
            QWidget#statusBar {
                background-color: #181818;
                border-top: 1px solid #2a2a2a;
            }

            QLabel {
                color: #d0d0d0;
                font-size: 14px;
            }
        """)

    # =========================
    # API
    # =========================
    def set_status(self, text):
        self.status.setText(text)

    def set_user(self, user):
        self.user.setText(user)
