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
        # SPI DISPLAY
        # =========================
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

        # =========================
        # STATE
        # =========================
        self.lock = threading.Lock()

        self.robot_hablando = False
        self.estado_texto = "Escuchando..."

        self.ojos_abiertos = True
        self.parpadeo_fin = 0
        self.proximo_parpadeo = time.time() + random.uniform(
            self.blink_min,
            self.blink_max
        )

        # Pupila animada (vida dentro del ojo)
        self.pupil_offset_x = 0
        self.pupil_offset_y = 0

        # =========================
        # FONT
        # =========================
        try:
            self.font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                16
            )
        except Exception:
            self.font = ImageFont.load_default()

        self.running = False

    # =========================
    # API
    # =========================
    def set_estado(self, texto: str):
        with self.lock:
            self.estado_texto = texto

    def set_hablando(self, speaking: bool):
        with self.lock:
            self.robot_hablando = speaking

    def stop(self):
        self.running = False

    # =========================
    # DIBUJO OJOS CON VIDA
    # =========================
    def dibujar_ojos(self, draw, cx, cy, sep, radio):

        if not self.ojos_abiertos:
            # ojos cerrados
            draw.line((cx-sep-radio, cy, cx-sep+radio, cy), fill="white", width=5)
            draw.line((cx+sep-radio, cy, cx+sep+radio, cy), fill="white", width=5)
            return

        # brillo (glow suave)
        glow_color = (180, 220, 255)

        for i in range(3):
            draw.ellipse(
                (cx-sep-radio-i, cy-radio-i, cx-sep+radio+i, cy+radio+i),
                outline=glow_color,
                width=1
            )
            draw.ellipse(
                (cx+sep-radio-i, cy-radio-i, cx+sep+radio+i, cy+radio+i),
                outline=glow_color,
                width=1
            )

        # ojo principal
        left_eye = (cx-sep-radio, cy-radio, cx-sep+radio, cy+radio)
        right_eye = (cx+sep-radio, cy-radio, cx+sep+radio, cy+radio)

        draw.ellipse(left_eye, outline="white", width=4)
        draw.ellipse(right_eye, outline="white", width=4)

        # pupila con micro movimiento (vida)
        px = self.pupil_offset_x
        py = self.pupil_offset_y

        pupil_r = 10

        for ox in [-sep, sep]:
            draw.ellipse(
                (cx+ox-5+px, cy-5+py, cx+ox+5+px, cy+5+py),
                fill="white"
            )
            draw.ellipse(
                (cx+ox-pupil_r+px, cy-pupil_r+py,
                 cx+ox+pupil_r+px, cy+pupil_r+py),
                fill="black"
            )

    # =========================
    # CARA
    # =========================
    def dibujar_cara(self):

        with self.lock:
            hablando = self.robot_hablando
            texto = self.estado_texto

        img = Image.new("RGB", (self.display.width, self.display.height), "black")
        draw = ImageDraw.Draw(img)

        cx = self.display.width // 2
        cy = self.display.height // 2 - 30

        radio = 35
        sep = 75

        # ojos
        self.dibujar_ojos(draw, cx, cy, sep, radio)

        # boca
        boca_y = cy + 75

        if hablando:
            apertura = random.randint(10, 18)
            draw.ellipse(
                (cx-15, boca_y-apertura, cx+15, boca_y+apertura),
                outline="white",
                width=4
            )
        else:
            draw.arc(
                (cx-30, boca_y-10, cx+30, boca_y+20),
                0, 180,
                fill="white",
                width=4
            )

        # texto
        draw.rectangle((0, 200, 320, 240), fill="black")
        draw.text(
            (10, 210),
            texto[:35],
            font=self.font,
            fill=(0, 255, 0) if not hablando else (255, 255, 0)
        )

        self.display.image(img)

    # =========================
    # LOOP (COMPATIBLE: loop o start)
    # =========================
    def loop(self, fps=None):
        self.start(fps)

    def start(self, fps=None):

        if fps:
            self.fps = fps

        self.running = True
        frame_time = 1 / self.fps

        while self.running:

            now = time.time()

            # parpadeo
            if now > self.proximo_parpadeo:
                self.ojos_abiertos = False
                self.parpadeo_fin = now + 0.15
                self.proximo_parpadeo = now + random.uniform(
                    self.blink_min,
                    self.blink_max
                )

            if self.parpadeo_fin and now > self.parpadeo_fin:
                self.ojos_abiertos = True
                self.parpadeo_fin = 0

            # movimiento sutil de pupila (como “vida”)
            self.pupil_offset_x = random.randint(-2, 2)
            self.pupil_offset_y = random.randint(-1, 1)

            self.dibujar_cara()

            time.sleep(frame_time)