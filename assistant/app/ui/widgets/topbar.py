import time

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout
)

from PyQt5.QtCore import (
    Qt,
    QTimer
)


class TopBar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(48)

        self.setObjectName("topbar")

        # =========================
        # WIDGETS
        # =========================
        self.title = QLabel("🤖 Robot OS")

        self.clock = QLabel("--:--")

        # =========================
        # LAYOUT
        # =========================
        layout = QHBoxLayout()

        layout.setContentsMargins(14, 6, 14, 6)

        layout.addWidget(self.title)

        layout.addStretch()

        layout.addWidget(self.clock)

        self.setLayout(layout)

        # =========================
        # STYLE
        # =========================
        self.setStyleSheet("""
            QWidget#topbar {
                background-color: #121212;
                border-bottom: 1px solid #2a2a2a;
            }

            QLabel {
                color: white;
                font-size: 16px;
            }
        """)

        # =========================
        # TIMER
        # =========================
        self.timer = QTimer()

        self.timer.timeout.connect(self.update_clock)

        self.timer.start(1000)

        self.update_clock()

    # =========================
    # CLOCK
    # =========================
    def update_clock(self):

        self.clock.setText(
            time.strftime("%H:%M:%S")
        )
