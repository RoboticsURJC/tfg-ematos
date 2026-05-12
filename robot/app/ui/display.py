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

        if config_path:
            with open(config_path) as f:
                self.config = json.load(f)
        else:
            self.config = {}

        cfg = self.config.get("display", {})

        self.fps = cfg.get("fps", 30)
        self.blink_min = cfg.get("blink_min_seconds", 4)
        self.blink_max = cfg.get("blink_max_seconds", 8)

        # SPI
        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
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

        self.lock = threading.Lock()

        self.estado = "Escuchando..."
        self.hablando = False

        self.ojos = True
        self.next_blink = time.time() + random.uniform(self.blink_min, self.blink_max)
        self.blink_end = 0

        # VIDA EN OJOS
        self.px = 0
        self.py = 0

        self.running = False

        try:
            self.font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                16
            )
        except:
            self.font = ImageFont.load_default()

    # =========================
    # API
    # =========================
    def set_estado(self, txt):
        with self.lock:
            self.estado = txt

    def set_hablando(self, val):
        with self.lock:
            self.hablando = val

    # =========================
    # OJOS CON BRILLO
    # =========================
    def draw_eyes(self, draw, cx, cy, sep):

        r = 35

        if not self.ojos:
            draw.line((cx-sep-r, cy, cx-sep+r, cy), fill="white", width=5)
            draw.line((cx+sep-r, cy, cx+sep+r, cy), fill="white", width=5)
            return

        # brillo (glow)
        for i in range(3):
            draw.ellipse(
                (cx-sep-r-i, cy-r-i, cx-sep+r+i, cy+r+i),
                outline=(120, 180, 255),
                width=1
            )
            draw.ellipse(
                (cx+sep-r-i, cy-r-i, cx+sep+r+i, cy+r+i),
                outline=(120, 180, 255),
                width=1
            )

        # ojos
        draw.ellipse((cx-sep-r, cy-r, cx-sep+r, cy+r), outline="white", width=4)
        draw.ellipse((cx+sep-r, cy-r, cx+sep+r, cy+r), outline="white", width=4)

        # pupilas vivas
        for ox in [-sep, sep]:

            draw.ellipse(
                (cx+ox-6+self.px, cy-6+self.py,
                 cx+ox+6+self.px, cy+6+self.py),
                fill="white"
            )

            draw.ellipse(
                (cx+ox-10+self.px, cy-10+self.py,
                 cx+ox+10+self.px, cy+10+self.py),
                fill="black"
            )

    # =========================
    # FRAME
    # =========================
    def draw(self):

        with self.lock:
            txt = self.estado
            talking = self.hablando

        img = Image.new("RGB", (320, 240), "black")
        draw = ImageDraw.Draw(img)

        cx, cy = 160, 100

        self.draw_eyes(draw, cx, cy, 75)

        # boca
        if talking:
            h = random.randint(10, 18)
            draw.ellipse((145, 160-h, 175, 160+h), outline="white", width=4)
        else:
            draw.arc((130, 150, 190, 180), 0, 180, fill="white", width=4)

        # texto
        draw.text((10, 210), txt[:40], font=self.font, fill=(0, 255, 0))

        self.display.image(img)

    # =========================
    # LOOP
    # =========================
    def start(self):

        self.running = True
        frame_time = 1 / self.fps

        while self.running:

            now = time.time()

            if now > self.next_blink:
                self.ojos = False
                self.blink_end = now + 0.15
                self.next_blink = now + random.uniform(self.blink_min, self.blink_max)

            if self.blink_end and now > self.blink_end:
                self.ojos = True
                self.blink_end = 0

            # vida en ojos
            self.px = random.randint(-2, 2)
            self.py = random.randint(-1, 1)

            self.draw()

            time.sleep(frame_time)