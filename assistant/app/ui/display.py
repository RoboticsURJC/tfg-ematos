
import random
import time
import json
import threading
import math

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
        # DISPLAY
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
        self.robot_hablando = False
        self.estado_texto = "Iniciando..."
        self.emotion = "neutral"

        self.running = False

        # blink
        self.next_blink = time.time() + random.uniform(self.blink_min, self.blink_max)
        self.blink_end = 0

        # para animación de boca
        self.animation_phase = 0

        # =========================
        # FONT
        # =========================
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
    def set_estado(self, text):
        self.estado_texto = text

    def set_talking(self, talking):
        self.robot_hablando = talking

    def set_emotion(self, emotion):
        self.emotion = emotion

    # =========================
    # START
    # =========================
    def start(self):
        if self.running:
            return

        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()

    # =========================
    # DRAW
    # =========================
    def draw(self, eyes_open=True):

        img = Image.new("RGB", (self.display.width, self.display.height), "black")
        draw = ImageDraw.Draw(img)

        cx = self.display.width // 2
        
        # =========================
        # POSICIONES
        # =========================
        cy = self.display.height // 2 - 10  # Centro de los ojos
        sep = 80  # Separación entre ojos
        eye_radius = 40  # Radio del ojo (más grande)
        
        # Cejas: centradas encima de cada ojo
        eyebrow_y = cy - 45  # Altura de las cejas
        eyebrow_width = 50   # Ancho de cada ceja
        eyebrow_height = 15  # Altura del arco
        
        # Boca
        mouth_y = cy + 55

        # Animación
        self.animation_phase += 1

        # =========================
        # EYEBROWS (CEJAS centradas sobre cada ojo)
        # =========================
        # Centro de cada ojo: cx - sep y cx + sep
        left_eye_cx = cx - sep
        right_eye_cx = cx + sep
        
        # ~ if self.emotion == "happy":
            # ~ # Cejas felices - arco convexo hacia arriba
            # ~ draw.arc((left_eye_cx - eyebrow_width, eyebrow_y - 10, 
                      # ~ left_eye_cx + eyebrow_width, eyebrow_y + eyebrow_height), 
                     # ~ 180, 360, fill="white", width=5)
            # ~ draw.arc((right_eye_cx - eyebrow_width, eyebrow_y - 10, 
                      # ~ right_eye_cx + eyebrow_width, eyebrow_y + eyebrow_height), 
                     # ~ 180, 360, fill="white", width=5)
        
        # ~ elif self.emotion == "sad":
            # ~ # Cejas tristes - arco hacia abajo
            # ~ draw.arc((left_eye_cx - eyebrow_width, eyebrow_y, 
                      # ~ left_eye_cx + eyebrow_width, eyebrow_y + eyebrow_height + 10), 
                     # ~ 0, 180, fill="white", width=5)
            # ~ draw.arc((right_eye_cx - eyebrow_width, eyebrow_y, 
                      # ~ right_eye_cx + eyebrow_width, eyebrow_y + eyebrow_height + 10), 
                     # ~ 0, 180, fill="white", width=5)
        
        # ~ elif self.emotion == "surprised":
            # ~ # Cejas sorprendidas - muy arriba
            # ~ draw.arc((left_eye_cx - eyebrow_width, eyebrow_y - 20, 
                      # ~ left_eye_cx + eyebrow_width, eyebrow_y + 5), 
                     # ~ 180, 360, fill="white", width=5)
            # ~ draw.arc((right_eye_cx - eyebrow_width, eyebrow_y - 20, 
                      # ~ right_eye_cx + eyebrow_width, eyebrow_y + 5), 
                     # ~ 180, 360, fill="white", width=5)
        
        # ~ elif self.emotion == "angry":
            # ~ # Cejas enfadadas - inclinadas hacia dentro
            # ~ draw.line((left_eye_cx - eyebrow_width, eyebrow_y - 5, 
                       # ~ left_eye_cx + 10, eyebrow_y + 15), fill="white", width=5)
            # ~ draw.line((right_eye_cx - 10, eyebrow_y - 5, 
                       # ~ right_eye_cx + eyebrow_width, eyebrow_y + 15), fill="white", width=5)
        
        # ~ elif self.emotion == "thinking":
            # ~ # Cejas pensativas - una más alta
            # ~ draw.arc((left_eye_cx - eyebrow_width, eyebrow_y - 10, 
                      # ~ left_eye_cx + eyebrow_width, eyebrow_y + eyebrow_height), 
                     # ~ 180, 360, fill="white", width=5)
            # ~ draw.arc((right_eye_cx - eyebrow_width, eyebrow_y - 20, 
                      # ~ right_eye_cx + eyebrow_width, eyebrow_y + 5), 
                     # ~ 180, 360, fill="white", width=5)
        
        # ~ else:  # NEUTRAL - arco suave
            # ~ draw.arc((left_eye_cx - eyebrow_width, eyebrow_y - 5, 
                      # ~ left_eye_cx + eyebrow_width, eyebrow_y + eyebrow_height), 
                     # ~ 180, 360, fill="white", width=5)
            # ~ draw.arc((right_eye_cx - eyebrow_width, eyebrow_y - 5, 
                      # ~ right_eye_cx + eyebrow_width, eyebrow_y + eyebrow_height), 
                     # ~ 180, 360, fill="white", width=5)

        # =========================
        # EYES
        # =========================
        if eyes_open:
            # Contorno de los ojos (círculos blancos)
            draw.ellipse((left_eye_cx - eye_radius, cy - eye_radius, 
                          left_eye_cx + eye_radius, cy + eye_radius), 
                         outline="white", width=5)
            draw.ellipse((right_eye_cx - eye_radius, cy - eye_radius, 
                          right_eye_cx + eye_radius, cy + eye_radius), 
                         outline="white", width=5)

            # Pupilas GRANDES y centradas (radio 28 de 40)
            pupil_radius = 28
            draw.ellipse((left_eye_cx - pupil_radius, cy - pupil_radius, 
                          left_eye_cx + pupil_radius, cy + pupil_radius), 
                         fill="black")
            draw.ellipse((right_eye_cx - pupil_radius, cy - pupil_radius, 
                          right_eye_cx + pupil_radius, cy + pupil_radius), 
                         fill="black")
            
            # BRILLO KAWAII (grande, abajo a la derecha)
            draw.ellipse((left_eye_cx + 12, cy + 8, left_eye_cx + 22, cy + 18), 
                        fill="white")
            draw.ellipse((right_eye_cx + 12, cy + 8, right_eye_cx + 22, cy + 18), 
                        fill="white")
            
            # Brillo pequeño secundario (super cute)
            draw.ellipse((left_eye_cx + 4, cy + 2, left_eye_cx + 8, cy + 6), 
                        fill="white")
            draw.ellipse((right_eye_cx + 4, cy + 2, right_eye_cx + 8, cy + 6), 
                        fill="white")

        else:
            # Ojos cerrados (línea curva kawaii)
            draw.arc((left_eye_cx - eye_radius, cy - 10, 
                      left_eye_cx + eye_radius, cy + 10), 
                     0, 180, fill="white", width=6)
            draw.arc((right_eye_cx - eye_radius, cy - 10, 
                      right_eye_cx + eye_radius, cy + 10), 
                     0, 180, fill="white", width=6)

        # =========================
        # MOUTH (Corregido para simular una "O" que se abre y cierra)
        # =========================
        if self.robot_hablando:
            # Calculamos la oscilación de base senoidal (modifica el 0.4 si quieres más velocidad)
            oscilacion = math.sin(self.animation_phase * 0.4)
            
            # El ancho y el alto oscilan juntos de manera proporcional
            mouth_w = 16 + int(8 * oscilacion)   # El radio horizontal varía entre 8 y 24 píxeles
            mouth_h = 16 + int(10 * oscilacion)  # El radio vertical varía entre 6 y 26 píxeles
            
            draw.ellipse((cx - mouth_w, mouth_y - mouth_h, 
                          cx + mouth_w, mouth_y + mouth_h), 
                         outline="white", width=4)

        else:
            if self.emotion == "happy":
                # Sonrisa grande
                draw.arc((cx - 45, mouth_y - 10, cx + 45, mouth_y + 25), 
                         0, 180, fill="white", width=5)
                # Sonrojo
                draw.ellipse((left_eye_cx - 25, cy + 25, left_eye_cx - 15, cy + 35), 
                             fill=(255, 100, 100), outline=None)
                draw.ellipse((right_eye_cx + 15, cy + 25, right_eye_cx + 25, cy + 35), 
                             fill=(255, 100, 100), outline=None)

            elif self.emotion == "sad":
                draw.arc((cx - 40, mouth_y, cx + 40, mouth_y + 30), 
                         180, 360, fill="white", width=4)

            elif self.emotion == "thinking":
                draw.line((cx - 30, mouth_y + 5, cx + 30, mouth_y + 5), 
                         fill="white", width=4)

            elif self.emotion == "surprised":
                draw.ellipse((cx - 15, mouth_y - 10, cx + 15, mouth_y + 10), 
                             outline="white", width=4)

            else:  # NEUTRAL
                draw.arc((cx - 35, mouth_y - 5, cx + 35, mouth_y + 18), 
                         0, 180, fill="white", width=4)

        # =========================
        # TEXT BAR
        # =========================
        draw.rectangle((0, 200, 320, 240), fill="black")
        
        texto_lower = self.estado_texto.lower()
        
        if "hablando" in texto_lower:
            draw.text((10, 208), self.estado_texto[:40], fill=(0, 255, 0), font=self.font)
        elif "pensando" in texto_lower:
            draw.text((10, 208), self.estado_texto[:40], fill=(255, 255, 0), font=self.font)
        elif "escuchado" in texto_lower:
            draw.text((10, 208), self.estado_texto[:40], fill=(0, 200, 255), font=self.font)
        else:
            draw.text((10, 208), self.estado_texto[:40], fill=(150, 255, 150), font=self.font)

        self.display.image(img)

    # =========================
    # LOOP
    # =========================
    def loop(self):

        fps = 1 / self.fps
        eyes_open = True

        while self.running:

            now = time.time()

            if now > self.next_blink:
                eyes_open = False
                self.blink_end = now + 0.15
                self.next_blink = now + random.uniform(self.blink_min, self.blink_max)

            if self.blink_end and now > self.blink_end:
                eyes_open = True
                self.blink_end = 0

            self.draw(eyes_open)
            time.sleep(fps)

