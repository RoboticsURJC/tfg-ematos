import time
import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw
import random

# ---------------- DISPLAY ----------------
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D23)
rst = digitalio.DigitalInOut(board.D24)

display = ili9341.ILI9341(
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    baudrate=24000000,
    width=320,
    height=240,
)

display.fill(0x000000)

# ---------------- DIBUJO CARA ----------------
def dibujar_cara(boca="sonrisa", ojos_abiertos=True):
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    cx = display.width // 2
    cy = display.height // 2 - 20

    radio_ojo = 38
    separacion = 80

    ojo_izq = (cx - separacion - radio_ojo, cy - radio_ojo,
               cx - separacion + radio_ojo, cy + radio_ojo)
    ojo_der = (cx + separacion - radio_ojo, cy - radio_ojo,
               cx + separacion + radio_ojo, cy + radio_ojo)

    # ---------- OJOS ----------
    if ojos_abiertos:
        draw.ellipse(ojo_izq, outline="white", width=4)
        draw.ellipse(ojo_der, outline="white", width=4)

        pupila_r = 8
        draw.ellipse((ojo_izq[0]+22, ojo_izq[1]+26,
                      ojo_izq[0]+22+pupila_r*2, ojo_izq[1]+26+pupila_r*2), fill="white")
        draw.ellipse((ojo_der[0]+22, ojo_der[1]+26,
                      ojo_der[0]+22+pupila_r*2, ojo_der[1]+26+pupila_r*2), fill="white")

        draw.ellipse((ojo_izq[0]+45, ojo_izq[1]+20,
                      ojo_izq[0]+50, ojo_izq[1]+25), fill="white")
        draw.ellipse((ojo_der[0]+45, ojo_der[1]+20,
                      ojo_der[0]+50, ojo_der[1]+25), fill="white")
    else:
        # ojos cerrados (líneas suaves)
        draw.line((ojo_izq[0], cy, ojo_izq[2], cy), fill="white", width=4)
        draw.line((ojo_der[0], cy, ojo_der[2], cy), fill="white", width=4)

    # ---------- BOCA ----------
    boca_y = cy + 70
    if boca == "sonrisa":
        draw.arc((cx-30, boca_y-10, cx+30, boca_y+20), 0, 180, fill="white", width=4)
    elif boca == "neutral":
        draw.line((cx-25, boca_y, cx+25, boca_y), fill="white", width=4)
    elif boca == "sorpresa":
        draw.ellipse((cx-10, boca_y-10, cx+10, boca_y+10), outline="white", width=4)

    display.image(img)


# ---------------- LOOP PRINCIPAL ----------------
proximo_parpadeo = time.time() + random.uniform(3, 5)

while True:
    ahora = time.time()

    if ahora >= proximo_parpadeo:
        # cerrar ojos
        dibujar_cara("sonrisa", ojos_abiertos=False)
        time.sleep(0.12)  # duración del parpadeo

        # abrir ojos
        dibujar_cara("sonrisa", ojos_abiertos=True)

        # nuevo parpadeo impredecible
        proximo_parpadeo = ahora + random.uniform(5, 10)

    else:
        dibujar_cara("sonrisa", ojos_abiertos=True)

    time.sleep(0.05)
