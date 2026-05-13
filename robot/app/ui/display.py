import time
import random
import json
import threading

import board
import busio
import digitalio

from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import ili9341


class FaceDisplay:

    def __init__(self, config_path=None):

        # =========================
        # CONFIG
        # =========================
        if config_path:
            with open(config_path) as f:
                self.config = json.load(f)
        else:
            self.config = {}

        display_cfg = self.config.get("display", {})

        self.fps = display_cfg.get("fps", 30)
        self.blink_min = display_cfg.get("blink_min_seconds", 4)
        self.blink_max = display_cfg.get("blink_max_seconds", 8)

        # =========================
        # SPI
        # =========================
        spi = busio.SPI(
            board.SCK,
            MOSI=board.MOSI
        )

        cs = digitalio.DigitalInOut(board.CE0)
        dc = digitalio.DigitalInOut(board.D23)
        rst = digitalio.DigitalInOut(board.D24)

        self.display = ili9341.ILI9341(
            spi,
            cs=cs,
            dc=dc,
            rst=rst,
            baudrate=24000000,
            width=320,
            height=240
        )

        # =========================
        # ESTADO
        # =========================
        self.robot_hablando = False
        self.estado_texto = "Iniciando..."

        self.parpadeo_fin = 0

        self.proximo_parpadeo = (
            time.time() + random.uniform(
                self.blink_min,
                self.blink_max
            )
        )

        self.running = False

        # =========================
        # FUENTE
        # =========================
        try:

            self.font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                16
            )

        except Exception:

            self.font = ImageFont.load_default()

    # =========================
    # API EXTERNA
    # =========================
    def set_estado(self, texto):
        self.estado_texto = texto

    def set_hablando(self, hablando):
        self.robot_hablando = hablando

    # =========================
    # START DISPLAY THREAD
    # =========================
    def start(self):

        if self.running:
            return

        self.running = True

        threading.Thread(
            target=self.loop,
            daemon=True
        ).start()

    # =========================
    # STOP
    # =========================
    def stop(self):
        self.running = False

    # =========================
    # DRAW
    # =========================
    def dibujar_cara(self, ojos_abiertos=True):

        img = Image.new(
            "RGB",
            (self.display.width, self.display.height),
            "black"
        )

        draw = ImageDraw.Draw(img)

        cx = self.display.width // 2
        cy = self.display.height // 2 - 30

        radio = 35
        sep = 75

        # =========================
        # OJOS
        # =========================
        if ojos_abiertos:

            # ojo izquierdo
            draw.ellipse(
                (
                    cx-sep-radio,
                    cy-radio,
                    cx-sep+radio,
                    cy+radio
                ),
                outline="white",
                width=4
            )

            # ojo derecho
            draw.ellipse(
                (
                    cx+sep-radio,
                    cy-radio,
                    cx+sep+radio,
                    cy+radio
                ),
                outline="white",
                width=4
            )

            # pupilas
            draw.ellipse(
                (
                    cx-sep-10,
                    cy-10,
                    cx-sep+10,
                    cy+10
                ),
                fill="white"
            )

            draw.ellipse(
                (
                    cx+sep-10,
                    cy-10,
                    cx+sep+10,
                    cy+10
                ),
                fill="white"
            )

        else:

            draw.line(
                (
                    cx-sep-radio,
                    cy,
                    cx-sep+radio,
                    cy
                ),
                fill="white",
                width=5
            )

            draw.line(
                (
                    cx+sep-radio,
                    cy,
                    cx+sep+radio,
                    cy
                ),
                fill="white",
                width=5
            )

        # =========================
        # BOCA
        # =========================
        boca_y = cy + 75

        if self.robot_hablando:

            apertura = random.randint(10, 18)

            draw.ellipse(
                (
                    cx-15,
                    boca_y-apertura,
                    cx+15,
                    boca_y+apertura
                ),
                outline="white",
                width=4
            )

        else:

            draw.arc(
                (
                    cx-30,
                    boca_y-10,
                    cx+30,
                    boca_y+20
                ),
                0,
                180,
                fill="white",
                width=4
            )

        # =========================
        # TEXTO
        # =========================
        draw.rectangle(
            (0, 200, 320, 240),
            fill="black"
        )

        color = (
            (255, 255, 0)
            if self.robot_hablando
            else (0, 255, 0)
        )

        draw.text(
            (10, 210),
            self.estado_texto[:35],
            font=self.font,
            fill=color
        )

        self.display.image(img)

    # =========================
    # LOOP
    # =========================
    def loop(self):

        frame_time = 1 / self.fps

        ojos_abiertos = True

        while self.running:

            now = time.time()

            # =========================
            # PARPADEO
            # =========================
            if now > self.proximo_parpadeo:

                ojos_abiertos = False

                self.parpadeo_fin = now + 0.15

                self.proximo_parpadeo = (
                    now + random.uniform(
                        self.blink_min,
                        self.blink_max
                    )
                )

            if self.parpadeo_fin and now > self.parpadeo_fin:

                ojos_abiertos = True
                self.parpadeo_fin = 0

            # =========================
            # DIBUJAR
            # =========================
            self.dibujar_cara(
                ojos_abiertos=ojos_abiertos
            )

            time.sleep(frame_time)