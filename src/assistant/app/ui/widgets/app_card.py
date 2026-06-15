from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout
)

from PyQt5.QtCore import (
    Qt,
    pyqtSignal
)


class AppCard(QFrame):

    clicked = pyqtSignal(str)

    def __init__(self, app_name, icon="🧩"):
        super().__init__()

        self.app_name = app_name

        self.setObjectName("appCard")

        self.setFixedSize(170, 170)

        self.setCursor(Qt.PointingHandCursor)

        self.icon = QLabel(icon)
        self.icon.setAlignment(Qt.AlignCenter)

        self.name = QLabel(app_name.capitalize())
        self.name.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()

        layout.addStretch()

        layout.addWidget(self.icon)

        layout.addWidget(self.name)

        layout.addStretch()

        self.setLayout(layout)

        self.setStyleSheet("""
            QFrame#appCard {
                background-color: #1e1e1e;
                border-radius: 22px;
                border: 2px solid #333;
            }

            QFrame#appCard:hover {
                background-color: #2d2d2d;
                border: 2px solid #666;
            }

            QLabel {
                color: white;
                font-size: 18px;
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.app_name)
