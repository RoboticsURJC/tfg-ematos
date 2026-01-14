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

emociones = ["feliz", "triste", "sorprendido", "guiño", "enojado"]

def dibujar_ojos_cejas_mov(emocion, parpado_ratio=0.0, ceja_offset=0):
    """
    Ojos huecos, borde grueso, parpadeo centrado, cejas moviéndose solo arriba del ojo
    ceja_offset: desplazamiento vertical de cejas para simular movimiento
    """
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)
    
    grosor_borde = 16
    margen_ceja = 35
    
    # Centro de la pantalla
    centro_x = display.width // 2
    centro_y = display.height // 2
    radio_ojo = 40
    separacion_ojo = 70
    
    # Coordenadas ojos
    ojo_izq = (
        centro_x - separacion_ojo - radio_ojo,
        centro_y - radio_ojo,
        centro_x - separacion_ojo + radio_ojo,
        centro_y + radio_ojo
    )
    ojo_der = (
        centro_x + separacion_ojo - radio_ojo,
        centro_y - radio_ojo,
        centro_x + separacion_ojo + radio_ojo,
        centro_y + radio_ojo
    )
    
    # Dibujar ojos huecos
    draw.ellipse(ojo_izq, outline="white", width=grosor_borde)
    draw.ellipse(ojo_der, outline="white", width=grosor_borde)
    
    # Parpadeo centrado
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
    
    # Cejas moviéndose solo encima de los ojos
    ceja_y_base = ojo_izq[1] - margen_ceja
    ceja_altura = ceja_y_base + 20
    
    # Ajuste de offset para movimiento natural
    ceja_y = ceja_y_base - ceja_offset  # sube o baja
    ceja_altura += -ceja_offset
    
    if emocion == "feliz":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=0, end=180, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=0, end=180, fill="white", width=5)
    elif emocion == "triste":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=180, end=360, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=180, end=360, fill="white", width=5)
    elif emocion == "sorprendido":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=0, end=180, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=0, end=180, fill="white", width=5)
    elif emocion == "enojado":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura), start=180, end=360, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=180, end=360, fill="white", width=5)
    elif emocion == "guiño":
        draw.line((ojo_izq[0], ojo_izq[3]-10, ojo_izq[2], ojo_izq[3]-10), fill="white", width=8)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura), start=0, end=180, fill="white", width=5)
    
    display.image(img)

# Animación principal
while True:
    emocion_actual = random.choice(emociones)
    for ratio in [0.0, 0.0, 0.2, 0.4, 0.2, 0.0]:  # parpadeo suave
        # Movimiento de cejas: offset aleatorio pequeño para naturalidad
        ceja_offset = random.randint(0, 8)  # suben o bajan 0-8 píxeles
        dibujar_ojos_cejas_mov(emocion_actual, parpado_ratio=ratio, ceja_offset=ceja_offset)
        time.sleep(0.15)
