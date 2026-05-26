# app/robot/display/renderer.py

from PIL import (
    Image,
    ImageDraw
)

from app.robot.display.emotions import Emotion


class FaceRenderer:
    """
    Renderer visual de la cara.
    """

    def __init__(self, width=320, height=240):

        self.width = width
        self.height = height

    # =========================================================
    # FRAME
    # =========================================================

    def render(
        self,
        emotion,
        eyes_open=True,
        mouth_open=0
    ):

        img = Image.new(
            "RGB",
            (self.width, self.height),
            "black"
        )

        draw = ImageDraw.Draw(img)

        cx = self.width // 2
        cy = self.height // 2 - 30

        self.draw_eyes(
            draw,
            cx,
            cy,
            emotion,
            eyes_open
        )

        self.draw_mouth(
            draw,
            cx,
            cy + 80,
            emotion,
            mouth_open
        )

        return img

    # =========================================================
    # EYES
    # =========================================================

    def draw_eyes(
        self,
        draw,
        cx,
        cy,
        emotion,
        eyes_open
    ):

        sep = 75
        radius = 35

        if eyes_open:

            for dx in (-sep, sep):

                # base eye
                draw.ellipse(
                    (
                        cx + dx - radius,
                        cy - radius,
                        cx + dx + radius,
                        cy + radius
                    ),
                    outline="white",
                    width=4
                )

                pupil_y = cy

                # thinking
                if emotion == Emotion.THINKING:
                    pupil_y -= 8

                # sad
                if emotion == Emotion.SAD:
                    pupil_y += 8

                draw.ellipse(
                    (
                        cx + dx - 10,
                        pupil_y - 10,
                        cx + dx + 10,
                        pupil_y + 10
                    ),
                    fill="white"
                )

                # angry eyebrow
                if emotion == Emotion.ERROR:

                    draw.line(
                        (
                            cx + dx - 30,
                            cy - 40,
                            cx + dx + 30,
                            cy - 20
                        ),
                        fill="red",
                        width=4
                    )

        else:

            for dx in (-sep, sep):

                draw.line(
                    (
                        cx + dx - radius,
                        cy,
                        cx + dx + radius,
                        cy
                    ),
                    fill="white",
                    width=5
                )

    # =========================================================
    # MOUTH
    # =========================================================

    def draw_mouth(
        self,
        draw,
        cx,
        y,
        emotion,
        mouth_open
    ):

        # speaking
        if mouth_open > 0:

            draw.ellipse(
                (
                    cx - 18,
                    y - mouth_open,
                    cx + 18,
                    y + mouth_open
                ),
                outline="white",
                width=4
            )

            return

        # happy
        if emotion == Emotion.HAPPY:

            draw.arc(
                (
                    cx - 35,
                    y - 10,
                    cx + 35,
                    y + 25
                ),
                0,
                180,
                fill="white",
                width=4
            )

        # sad
        elif emotion == Emotion.SAD:

            draw.arc(
                (
                    cx - 35,
                    y,
                    cx + 35,
                    y + 25
                ),
                180,
                360,
                fill="white",
                width=4
            )

        # thinking
        elif emotion == Emotion.THINKING:

            draw.line(
                (
                    cx - 20,
                    y,
                    cx + 20,
                    y
                ),
                fill="white",
                width=4
            )

        # error
        elif emotion == Emotion.ERROR:

            draw.rectangle(
                (
                    cx - 25,
                    y - 5,
                    cx + 25,
                    y + 5
                ),
                outline="red",
                width=3
            )

        # sleep
        elif emotion == Emotion.SLEEP:

            draw.line(
                (
                    cx - 15,
                    y,
                    cx + 15,
                    y
                ),
                fill="blue",
                width=3
            )

        # neutral
        else:

            draw.arc(
                (
                    cx - 30,
                    y - 5,
                    cx + 30,
                    y + 20
                ),
                0,
                180,
                fill="white",
                width=4
            )
