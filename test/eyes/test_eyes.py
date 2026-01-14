import random
import time
import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw

# --- Configuración SPI y display ---
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D23)
rst = digitalio.DigitalInOut(board.D24)

# Display horizontal (landscape)
display = ili9341.ILI9341(
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    baudrate=24000000,
    width=320,
    height=240,
    rotation=90  # landscape
)

display.fill(0x000000)

# Lista de emociones
emociones = ["feliz", "triste", "sorprendido", "guiño", "enojado"]

def dibujar_ojos_final_horizontales(emocion, parpado_ratio=0.0):
    """
    Ojos huecos, borde grueso, parpadeo natural, cejas arqueadas arriba.
    parpado_ratio: 0.0 = abierto, 1.0 = cerrado
    """
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)
    
    grosor_borde = 14
    margen_ceja = 25
    
    # Coordenadas relativas al centro
    centro_x = display.width // 2
    centro_y = display.height // 2
    radio_ojo = 30
    separacion_ojo = 60
    
    # Ojo izquierdo
    ojo_izq = (
        centro_x - separacion_ojo - radio_ojo,
        centro_y - radio_ojo,
        centro_x - separacion_ojo + radio_ojo,
        centro_y + radio_ojo
    )
    # Ojo derecho
    ojo_der = (
        centro_x + separacion_ojo - radio_ojo,
        centro_y - radio_ojo,
        centro_x + separacion_ojo + radio_ojo,
        centro_y + radio_ojo
    )
    
    # Dibujar ojos huecos
    draw.ellipse(ojo_izq, outline="white", width=grosor_borde)
    draw.ellipse(ojo_der, outline="white", width=grosor_borde)
    
    # Parpadeo centrado (linea negra sobre el ojo, doblando el círculo)
    if parpado_ratio > 0:
        delta = int(radio_ojo * parpado_ratio)
        draw.line(
            (ojo_izq[0]+grosor_borde//2, centro_y - delta,
             ojo_izq[2]-grosor_borde//2, centro_y - delta),
            fill="black", width=grosor_borde
        )
        draw.line(
            (ojo_der[0]+grosor_borde//2, centro_y - delta,
             ojo_der[2]-grosor_borde//2, centro_y - delta),
            fill="black", width=grosor_borde
        )
    
    # Cejas arqueadas siempre arriba del ojo
    ceja_y = ojo_izq[1] - margen_ceja
    ceja_altura = ceja_y + 20
    
    if emocion == "feliz":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=0, end=180, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=0, end=180, fill="white", width=4)
    elif emocion == "triste":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=180, end=360, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=180, end=360, fill="white", width=4)
    elif emocion == "sorprendido":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=0, end=180, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=0, end=180, fill="white", width=4)
    elif emocion == "enojado":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=180, end=360, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=180, end=360, fill="white", width=4)
    elif emocion == "guiño":
        draw.line((ojo_izq[0], ojo_izq[3]-10, ojo_izq[2], ojo_izq[3]-10), fill="white", width=6)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=0, end=180, fill="white", width=4)
    
    display.image(img)

# Animación principal
while True:
    emocion_actual = random.choice(emociones)
    
    # Parpadeo suave
    for ratio in [0.0, 0.0, 0.2, 0.4, 0.2, 0.0]:
        dibujar_ojos_final_horizontales(emocion_actual, parpado_ratio=ratio)
        time.sleep(0.15)
