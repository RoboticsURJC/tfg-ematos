import random
import time
import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw

# Configuración del SPI y display
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
    width=240,
    height=320,
)

display.fill(0x000000)

# Lista de emociones
emociones = ["feliz", "triste", "sorprendido", "guiño", "enojado"]

def dibujar_ojos_huecos(emocion, pupila_offset_x=0, pupila_offset_y=0, parpado_ratio=0.0):
    """
    Dibuja ojos huecos con pupilas movibles y parpadeo.
    parpado_ratio: 0.0 = ojo abierto, 1.0 = ojo cerrado
    """
    img = Image.new("RGB", (240, 320), "black")
    draw = ImageDraw.Draw(img)
    
    # Coordenadas ojos
    ojo_izq = (50, 100, 110, 160)
    ojo_der = (130, 100, 190, 160)
    
    # Dibujar contornos de ojos (huecos)
    draw.ellipse(ojo_izq, outline="white", width=4)
    draw.ellipse(ojo_der, outline="white", width=4)
    
    # Pupilas (dentro de los ojos)
    draw.ellipse((75 + pupila_offset_x, 125 + pupila_offset_y, 95 + pupila_offset_x, 145 + pupila_offset_y), fill="white")
    draw.ellipse((155 + pupila_offset_x, 125 + pupila_offset_y, 175 + pupila_offset_x, 145 + pupila_offset_y), fill="white")
    
    # Párpados para parpadeo
    parpado_alto = int(100 + 60 * parpado_ratio / 2)
    parpado_bajo = int(160 - 60 * parpado_ratio / 2)
    draw.rectangle((50, 100, 110, parpado_alto), fill="black")
    draw.rectangle((50, parpado_bajo, 110, 160), fill="black")
    draw.rectangle((130, 100, 190, parpado_alto), fill="black")
    draw.rectangle((130, parpado_bajo, 190, 160), fill="black")
    
    # Cejas según emoción
    if emocion == "feliz":
        draw.line((50, 90, 110, 95), fill="white", width=4)
        draw.line((130, 95, 190, 90), fill="white", width=4)
    elif emocion == "triste":
        draw.line((50, 95, 110, 90), fill="white", width=4)
        draw.line((130, 90, 190, 95), fill="white", width=4)
    elif emocion == "sorprendido":
        draw.line((50, 85, 110, 85), fill="white", width=4)
        draw.line((130, 85, 190, 85), fill="white", width=4)
    elif emocion == "enojado":
        draw.line((50, 95, 110, 90), fill="white", width=4)
        draw.line((130, 90, 190, 95), fill="white", width=4)
    elif emocion == "guiño":
        draw.line((50, 130, 110, 130), fill="white", width=6)  # ojo izquierdo cerrado
        draw.line((130, 90, 190, 85), fill="white", width=4)
    
    display.image(img)

# Animación principal
while True:
    emocion_actual = random.choice(emociones)
    
    # Pupilas que se mueven de lado a lado
    for offset in range(-5, 6, 1):
        parpado_ratio = random.choice([0.0, 0.0, 0.0, 0.5, 1.0])  # parpadeo aleatorio
        dibujar_ojos_huecos(emocion_actual, pupila_offset_x=offset, parpado_ratio=parpado_ratio)
        time.sleep(0.1)
    for offset in range(5, -6, -1):
        parpado_ratio = random.choice([0.0, 0.0, 0.0, 0.5, 1.0])
        dibujar_ojos_huecos(emocion_actual, pupila_offset_x=offset, parpado_ratio=parpado_ratio)
        time.sleep(0.1)
