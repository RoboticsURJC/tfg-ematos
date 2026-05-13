import time
import random
import json

import board
import busio
import digitalio

from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import ili9341


## @file display.py
#  @brief Control visual del rostro del asistente.
#
#  Gestiona:
#   - pantalla SPI ILI9341
#   - animación facial
#   - texto de estado
#   - parpadeos automáticos
#   - animación de boca


class FaceDisplay:
    """
    Controla la pantalla física SPI y renderiza
    la cara animada del asistente.
    """

    # =========================
    # INIT
    # =========================
    def __init__(self, config_path=None):

        # =========================
        # CONFIG
        # =========================
        self.config = {}

        if config_path:
            try:
                with open(config_path, "r") as f:
                    self.config = json.load(f)
            except Exception:
                print("No se pudo cargar config.json")

        display_cfg = self.config.get("display", {})

        self.fps = display_cfg.get("fps", 30)

        self.blink_min = display_cfg.get(
            "blink_min_seconds",
            4
        )

        self.blink_max = display_cfg.get(
            "blink_max_seconds",
            8
        )

        # =========================
        # SPI SETUP
        # =========================
        spi = busio.SPI(
            board.SCK,
            MOSI=board.MOSI
        )

        cs = digitalio.DigitalInOut(board.CE0)
        dc = digitalio.DigitalInOut(board.D23)
        rst = digitalio.DigitalInOut(board.D24)

        # =========================
        # DISPLAY
        # =========================
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
        # ESTADO INTERNO
        # =========================
        self.robot_hablando = False

        self.estado_texto = "Inicializando..."

        self.ojos_abiertos = True

        self.parpadeo_fin = 0

        self.proximo_parpadeo = (
            time.time() +
            random.uniform(
                self.blink_min,
                self.blink_max
            )
        )

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
    def set_estado(self, texto: str):
        """
        Actualiza texto inferior.
        """
        self.estado_texto = texto

    def set_hablando(self, speaking: bool):
        """
        Cambia estado de animación de boca.
        """
        self.robot_hablando = speaking

    # =========================
    # DIBUJO COMPLETO
    # =========================
    def dibujar_cara(self):

        # Crear canvas
        img = Image.new(
            "RGB",
            (
                self.display.width,
                self.display.height
            ),
            "black"
        )

        draw = ImageDraw.Draw(img)

        # =========================
        # GEOMETRÍA BASE
        # =========================
        cx = self.display.width // 2
        cy = self.display.height // 2 - 30

        radio = 35
        separacion = 75

        # =========================
        # OJOS
        # =========================
        if self.ojos_abiertos:

            # OJO IZQUIERDO
            draw.ellipse(
                (
                    cx - separacion - radio,
                    cy - radio,
                    cx - separacion + radio,
                    cy + radio
                ),
                outline="white",
                width=4
            )

            # OJO DERECHO
            draw.ellipse(
                (
                    cx + separacion - radio,
                    cy - radio,
                    cx + separacion + radio,
                    cy + radio
                ),
                outline="white",
                width=4
            )

            # =========================
            # PUPILAS
            # =========================
            draw.ellipse(
                (
                    cx - separacion - 10,
                    cy - 10,
                    cx - separacion + 10,
                    cy + 10
                ),
                fill="white"
            )

            draw.ellipse(
                (
                    cx + separacion - 10,
                    cy - 10,
                    cx + separacion + 10,
                    cy + 10
                ),
                fill="white"
            )

            # =========================
            # BRILLOS
            # =========================
            draw.ellipse(
                (
                    cx - separacion + 8,
                    cy - 18,
                    cx - separacion + 16,
                    cy - 10
                ),
                fill="white"
            )

            draw.ellipse(
                (
                    cx + separacion + 8,
                    cy - 18,
                    cx + separacion + 16,
                    cy - 10
                ),
                fill="white"
            )

        else:

            # OJOS CERRADOS
            draw.line(
                (
                    cx - separacion - radio,
                    cy,
                    cx - separacion + radio,
                    cy
                ),
                fill="white",
                width=5
            )

            draw.line(
                (
                    cx + separacion - radio,
                    cy,
                    cx + separacion + radio,
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
                    cx - 18,
                    boca_y - apertura,
                    cx + 18,
                    boca_y + apertura
                ),
                outline="white",
                width=4
            )

        else:

            # sonrisa
            draw.arc(
                (
                    cx - 30,
                    boca_y - 10,
                    cx + 30,
                    boca_y + 20
                ),
                start=0,
                end=180,
                fill="white",
                width=4
            )

        # =========================
        # PANEL TEXTO
        # =========================
        draw.rectangle(
            (
                0,
                200,
                320,
                240
            ),
            fill="black"
        )

        # color dinámico
        text_color = (
            (255, 255, 0)
            if self.robot_hablando
            else (0, 255, 0)
        )

        draw.text(
            (10, 210),
            self.estado_texto[:35],
            font=self.font,
            fill=text_color
        )

        # =========================
        # ENVIAR A DISPLAY
        # =========================
        self.display.image(img)

    # =========================
    # PARPADEO
    # =========================
    def actualizar_parpadeo(self):

        ahora = time.time()

        # iniciar parpadeo
        if ahora > self.proximo_parpadeo:

            self.ojos_abiertos = False

            self.parpadeo_fin = ahora + 0.15

            self.proximo_parpadeo = (
                ahora +
                random.uniform(
                    self.blink_min,
                    self.blink_max
                )
            )

        # terminar parpadeo
        if (
            self.parpadeo_fin and
            ahora > self.parpadeo_fin
        ):
            self.ojos_abiertos = True
            self.parpadeo_fin = 0

    # =========================
    # LOOP PRINCIPAL
    # =========================
    def loop(self, fps=None):
        """
        Loop principal de renderizado.
        """

        if fps is None:
            fps = self.fps

        frame_time = 1 / fps

        while True:

            # actualizar animaciones
            self.actualizar_parpadeo()

            # render
            self.dibujar_cara()

            # FPS
            time.sleep(frame_time)