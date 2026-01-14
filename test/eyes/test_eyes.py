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

def dibujar_ojos_arqueados(emocion, parpado_ratio=0.0):
    """
    Dibuja ojos huecos con parpadeo arqueado centrado
    parpado_ratio: 0.0 = abierto, 1.0 = cerrado
    """
    img = Image.new("RGB", (240, 320), "black")
    draw = ImageDraw.Draw(img)
    
    grosor = 6  # grosor del borde
    
    # Coordenadas ojos
    ojo_izq = (50, 100, 110, 160)
    ojo_der = (130, 100, 190, 160)
    
    # Dibujar contornos de ojos
    draw.ellipse(ojo_izq, outline="white", width=grosor)
    draw.ellipse(ojo_der, outline="white", width=grosor)
    
    # Parpadeo centrado (doblando el círculo por la mitad)
    if parpado_ratio > 0:
        altura_ojo = ojo_izq[3] - ojo_izq[1]
        delta = int(altura_ojo * parpado_ratio / 2)
        
        # Ojo izquierdo
        draw.arc(
            (ojo_izq[0], ojo_izq[1] + delta, ojo_izq[2], ojo_izq[3] - delta),
            start=0, end=180, fill="black", width=grosor
        )
        # Ojo derecho
        draw.arc(
            (ojo_der[0], ojo_der[1] + delta, ojo_der[2], ojo_der[3] - delta),
            start=0, end=180, fill="black", width=grosor
        )
    
    # Cejas arqueadas según emoción
    if emocion == "feliz":
        draw.arc((50, 80, 110, 100), start=0, end=180, fill="white", width=4)
        draw.arc((130, 80, 190, 100), start=0, end=180, fill="white", width=4)
    elif emocion == "triste":
        draw.arc((50, 95, 110, 115), start=180, end=360, fill="white", width=4)
        draw.arc((130, 95, 190, 115), start=180, end=360, fill="white", width=4)
    elif emocion == "sorprendido":
        draw.arc((50, 85, 110, 105), start=0, end=180, fill="white", width=4)
        draw.arc((130, 85, 190, 105), start=0, end=180, fill="white", width=4)
    elif emocion == "enojado":
        draw.arc((50, 95, 110, 115), start=180, end=360, fill="white", width=4)
        draw.arc((130, 95, 190, 115), start=180, end=360, fill="white", width=4)
    elif emocion == "guiño":
        draw.arc((50, 130, 110, 150), start=0, end=180, fill="white", width=6)  # ojo izquierdo cerrado
        draw.arc((130, 85, 190, 105), start=0, end=180, fill="white", width=4)
    
    display.image(img)

# Animación principal
while True:
    emocion_actual = random.choice(emociones)
    
    # Parpadeo suave
    for ratio in [0.0, 0.0, 0.2, 0.5, 0.0]:  # abre-cierra
        dibujar_ojos_arqueados(emocion_actual, parpado_ratio=ratio)
        time.sleep(0.15)
