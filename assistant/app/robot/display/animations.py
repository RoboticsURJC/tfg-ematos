# app/robot/display/animations.py

import random
import time


class BlinkAnimation:
    """
    Sistema de parpadeo automático.
    """

    def __init__(
        self,
        min_seconds=4,
        max_seconds=8
    ):

        self.min_seconds = min_seconds
        self.max_seconds = max_seconds

        self.eyes_open = True

        self.blink_end = 0

        self.next_blink = (
            time.time()
            + random.uniform(
                self.min_seconds,
                self.max_seconds
            )
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):

        now = time.time()

        # iniciar parpadeo
        if now >= self.next_blink:

            self.eyes_open = False

            self.blink_end = now + 0.15

            self.next_blink = (
                now
                + random.uniform(
                    self.min_seconds,
                    self.max_seconds
                )
            )

        # terminar parpadeo
        if (
            self.blink_end
            and now >= self.blink_end
        ):

            self.eyes_open = True

            self.blink_end = 0

        return self.eyes_open


# =============================================================
# MOUTH ANIMATION
# =============================================================

class MouthAnimation:

    def __init__(self):

        self.talking = False

    def set_talking(self, value):

        self.talking = value

    def get_open_amount(self):

        if not self.talking:
            return 0

        return random.randint(8, 18)
