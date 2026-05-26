# app/robot/display/face_display.py

import time
import json
import threading

import board
import busio
import digitalio

from PIL import (
    ImageDraw,
    ImageFont
)

from adafruit_rgb_display import ili9341

from app.robot.display.renderer import (
    FaceRenderer
)

from app.robot.display.animations import (
    BlinkAnimation,
    MouthAnimation
)

from app.robot.display.emotions import (
    Emotion
)


class FaceDisplay:
    """
    Cara emocional SPI del robot.
    """

    def __init__(self, config_path=None):

        # =====================================================
        # CONFIG
        # =====================================================

        self.config = {}

        if config_path:

            with open(config_path, "r") as f:
                self.config = json.load(f)

        display_cfg = self.config.get(
            "display",
            {}
        )

        self.fps = display_cfg.get(
            "fps",
            30
        )

        # =====================================================
        # SPI
        # =====================================================

        spi = busio.SPI(
            board.SCK,
            MOSI=board.MOSI
        )

        cs = digitalio.DigitalInOut(
            board.CE0
        )

        dc = digitalio.DigitalInOut(
            board.D23
        )

        rst = digitalio.DigitalInOut(
            board.D24
        )

        self.display = ili9341.ILI9341(
            spi,
            cs=cs,
            dc=dc,
            rst=rst,
            baudrate=24000000,
            width=320,
            height=240
        )

        # =====================================================
        # RENDERER
        # =====================================================

        self.renderer = FaceRenderer()

        # =====================================================
        # ANIMATIONS
        # =====================================================

        self.blink = BlinkAnimation()

        self.mouth = MouthAnimation()

        # =====================================================
        # STATE
        # =====================================================

        self.running = False

        self.emotion = Emotion.NEUTRAL

        self.estado_texto = "Sistema iniciado"

        self.user = None

        # =====================================================
        # FONT
        # =====================================================

        try:

            self.font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                16
            )

        except Exception:

            self.font = ImageFont.load_default()

    # =========================================================
    # API
    # =========================================================

    def set_estado(self, texto):

        self.estado_texto = texto

    def set_user(self, user):

        self.user = user

    def set_emotion(self, emotion):

        self.emotion = emotion

    def set_hablando(self, speaking):

        self.mouth.set_talking(speaking)

    # =========================================================
    # START
    # =========================================================

    def start(self):

        if self.running:
            return

        self.running = True

        threading.Thread(
            target=self.loop,
            daemon=True
        ).start()

    # =========================================================
    # STOP
    # =========================================================

    def stop(self):

        self.running = False

    # =========================================================
    # DRAW UI
    # =========================================================

    def draw_overlay(self, img):

        draw = ImageDraw.Draw(img)

        draw.rectangle(
            (0, 200, 320, 240),
            fill="black"
        )

        text = ""

        if self.user:
            text += f"{self.user} › "

        text += self.estado_texto

        color = (0, 255, 0)

        if self.emotion == Emotion.ERROR:
            color = (255, 0, 0)

        if self.emotion == Emotion.THINKING:
            color = (255, 255, 0)

        draw.text(
            (10, 210),
            text[:40],
            fill=color,
            font=self.font
        )

    # =========================================================
    # LOOP
    # =========================================================

    def loop(self):

        frame_time = 1 / self.fps

        while self.running:

            eyes_open = self.blink.update()

            mouth_open = (
                self.mouth.get_open_amount()
            )

            img = self.renderer.render(
                emotion=self.emotion,
                eyes_open=eyes_open,
                mouth_open=mouth_open
            )

            self.draw_overlay(img)

            self.display.image(img)

            time.sleep(frame_time)
