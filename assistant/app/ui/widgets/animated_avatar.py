import random

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPen
)

from PyQt5.QtCore import (
    Qt,
    QTimer
)


class AnimatedAvatar(QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumSize(240, 240)

        self.eye_open = True

        self.mouth_open = False

        self.emotion = "neutral"

        # =========================
        # BLINK TIMER
        # =========================
        self.blink_timer = QTimer()

        self.blink_timer.timeout.connect(self.blink)

        self.blink_timer.start(3500)

        # =========================
        # TALK TIMER
        # =========================
        self.talk_timer = QTimer()

        self.talk_timer.timeout.connect(self.animate_talk)

    # =========================
    # API
    # =========================
    def set_emotion(self, emotion):
        self.emotion = emotion
        self.update()

    def set_talking(self, talking):

        if talking:
            self.talk_timer.start(120)
        else:
            self.talk_timer.stop()
            self.mouth_open = False
            self.update()

    # =========================
    # BLINK
    # =========================
    def blink(self):

        self.eye_open = False

        self.update()

        QTimer.singleShot(
            120,
            self.open_eyes
        )

    def open_eyes(self):

        self.eye_open = True

        self.update()

    # =========================
    # TALK
    # =========================
    def animate_talk(self):

        self.mouth_open = not self.mouth_open

        self.update()

    # =========================
    # PAINT
    # =========================
    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#111111")
        )

        pen = QPen(QColor("white"))

        pen.setWidth(5)

        painter.setPen(pen)

        w = self.width()
        h = self.height()

        eye_y = h // 2 - 40

        # =========================
        # EYES
        # =========================
        if self.eye_open:

            painter.drawEllipse(
                w // 2 - 80,
                eye_y,
                50,
                50
            )

            painter.drawEllipse(
                w // 2 + 30,
                eye_y,
                50,
                50
            )

        else:

            painter.drawLine(
                w // 2 - 80,
                eye_y + 25,
                w // 2 - 30,
                eye_y + 25
            )

            painter.drawLine(
                w // 2 + 30,
                eye_y + 25,
                w // 2 + 80,
                eye_y + 25
            )

        # =========================
        # MOUTH
        # =========================
        mouth_y = h // 2 + 60

        if self.mouth_open:

            painter.drawEllipse(
                w // 2 - 20,
                mouth_y,
                40,
                26
            )

        else:

            if self.emotion == "happy":

                painter.drawArc(
                    w // 2 - 40,
                    mouth_y - 10,
                    80,
                    40,
                    0,
                    -180 * 16
                )

            elif self.emotion == "sad":

                painter.drawArc(
                    w // 2 - 40,
                    mouth_y + 10,
                    80,
                    40,
                    0,
                    180 * 16
                )

            else:

                painter.drawLine(
                    w // 2 - 35,
                    mouth_y + 10,
                    w // 2 + 35,
                    mouth_y + 10
                )
