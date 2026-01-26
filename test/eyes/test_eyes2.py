import time
import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw
import random

# Configuración SPI y display
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

def dibujar_ojos_parpadeo(parpado_ratio):
    """Dibuja ojos con parpadeo gradual y arco dinámico."""
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    grosor_borde = 16
    centro_x = display.width // 2
    centro_y = display.height // 2
    radio_ojo = 40
    separacion_ojo = 70

    ojo_izq = (centro_x - separacion_ojo - radio_ojo, centro_y - radio_ojo,
               centro_x - separacion_ojo + radio_ojo, centro_y + radio_ojo)
    ojo_der = (centro_x + separacion_ojo - radio_ojo, centro_y - radio_ojo,
               centro_x + separacion_ojo + radio_ojo, centro_y + radio_ojo)

    alto_ojo = ojo_izq[3] - ojo_izq[1]
    delta = int((alto_ojo / 2) * parpado_ratio)

    izq_x0 = int(ojo_izq[0] + grosor_borde // 2)
    izq_x1 = int(ojo_izq[2] - grosor_borde // 2)
    der_x0 = int(ojo_der[0] + grosor_borde // 2)
    der_x1 = int(ojo_der[2] - grosor_borde // 2)

    centro_y_ojo = (ojo_izq[1] + ojo_izq[3]) // 2

    # Dibujar contorno siempre
    draw.ellipse(ojo_izq, outline="white", width=grosor_borde)
    draw.ellipse(ojo_der, outline="white", width=grosor_borde)

    # Cubrir párpados según ratio
    draw.rectangle((izq_x0, ojo_izq[1], izq_x1, centro_y_ojo - delta), fill="black")
    draw.rectangle((izq_x0, centro_y_ojo + delta, izq_x1, ojo_izq[3]), fill="black")
    draw.rectangle((der_x0, ojo_der[1], der_x1, centro_y_ojo - delta), fill="black")
    draw.rectangle((der_x0, centro_y_ojo + delta, der_x1, ojo_der[3]), fill="black")

    # Arco dinámico: aparece gradualmente mientras cierra
    if parpado_ratio > 0.7:  # empieza a aparecer
        arco_altura = int(4 + 6 * (parpado_ratio - 0.7)/0.3)  # sube hasta 10 px
        draw.arc(ojo_izq, start=0, end=180, fill="white", width=arco_altura)
        draw.arc(ojo_der, start=0, end=180, fill="white", width=arco_altura)

    display.image(img)

# Animación de parpadeo con intervalos aleatorios
ultimo_parpadeo = time.time()
parpadeo_intervalo = random.uniform(2, 5)  # segundos

while True:
    ahora = time.time()
    if ahora - ultimo_parpadeo > parpadeo_intervalo:
        # Parpadeo completo con suavidad
        for step in range(21):
            ratio = step / 20
            dibujar_ojos_parpadeo(ratio)
            time.sleep(0.03)
        for step in range(20, -1, -1):
            ratio = step / 20
            dibujar_ojos_parpadeo(ratio)
            time.sleep(0.03)
        ultimo_parpadeo = ahora
        parpadeo_intervalo = random.uniform(2, 5)
    else:
        # Ojos abiertos
        dibujar_ojos_parpadeo(0.0)
        time.sleep(0.1)
  