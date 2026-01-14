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

emociones = ["feliz", "triste", "sorprendido", "guiño", "enojado"]

def dibujar_ojos_naturales(emocion, parpado_ratio=0.0):
    """
    Ojos huecos con borde grueso y parpadeo natural.
    parpado_ratio: 0.0 = abierto, 1.0 = cerrado
    """
    img = Image.new("RGB", (240, 320), "black")
    draw = ImageDraw.Draw(img)
    
    grosor_borde = 12  # ojo bien grueso
    margen_ceja = 15   # espacio entre ojo y ceja
    
    # Coordenadas de los ojos
    ojo_izq = (50, 100, 110, 160)
    ojo_der = (130, 100, 190, 160)
    
    # Dibujar contornos gruesos
    draw.ellipse(ojo_izq, outline="white", width=grosor_borde)
    draw.ellipse(ojo_der, outline="white", width=grosor_borde)
    
    # Parpadeo centrado (simula pliegue por el medio, sin deformar el contorno)
    if parpado_ratio > 0:
        altura_ojo = ojo_izq[3] - ojo_izq[1]
        delta = int(altura_ojo * parpado_ratio / 2)
        draw.line((ojo_izq[0]+grosor_borde//2, ojo_izq[1]+delta,
                   ojo_izq[2]-grosor_borde//2, ojo_izq[1]+delta), fill="black", width=grosor_borde)
        draw.line((ojo_der[0]+grosor_borde//2, ojo_der[1]+delta,
                   ojo_der[2]-grosor_borde//2, ojo_der[1]+delta), fill="black", width=grosor_borde)
    
    # Cejas arqueadas siempre sobre el ojo
    ceja_altura = ojo_izq[1] - margen_ceja
    ancho_ojos = ojo_izq[2] - ojo_izq[0]
    
    if emocion == "feliz":
        draw.arc((ojo_izq[0], ceja_altura, ojo_izq[2], ceja_altura+20), start=0, end=180, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_altura, ojo_der[2], ceja_altura+20), start=0, end=180, fill="white", width=4)
    elif emocion == "triste":
        draw.arc((ojo_izq[0], ceja_altura+10, ojo_izq[2], ceja_altura+30), start=180, end=360, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_altura+10, ojo_der[2], ceja_altura+30), start=180, end=360, fill="white", width=4)
    elif emocion == "sorprendido":
        draw.arc((ojo_izq[0], ceja_altura, ojo_izq[2], ceja_altura+20), start=0, end=180, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_altura, ojo_der[2], ceja_altura+20), start=0, end=180, fill="white", width=4)
    elif emocion == "enojado":
        draw.arc((ojo_izq[0], ceja_altura+5, ojo_izq[2], ceja_altura+25), start=180, end=360, fill="white", width=4)
        draw.arc((ojo_der[0], ceja_altura+5, ojo_der[2], ceja_altura+25), start=180, end=360, fill="white", width=4)
    elif emocion == "guiño":
        draw.line((ojo_izq[0], ojo_izq[3]-10, ojo_izq[2], ojo_izq[3]-10), fill="white", width=6)
        draw.arc((ojo_der[0], ceja_altura, ojo_der[2], ceja_altura+20), start=0, end=180, fill="white", width=4)
    
    display.image(img)

# Animación
while True:
    emocion_actual = random.choice(emociones)
    # Parpadeo más natural
    for ratio in [0.0, 0.0, 0.2, 0.4, 0.2, 0.0]:
        dibujar_ojos_naturales(emocion_actual, parpado_ratio=ratio)
        time.sleep(0.15)
