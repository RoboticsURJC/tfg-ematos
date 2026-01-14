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

def dibujar_ojos_parpadeo_cejas(emocion, parpado_ratio=0.0, ceja_offset=0):
    """
    Ojos grandes huecos, parpadeo real (doblando ojo), cejas moviéndose solo encima.
    """
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)
    
    grosor_borde = 16
    margen_ceja = 35
    
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
    
    # Dibujar ojo hueco
    draw.ellipse(ojo_izq, outline="white", width=grosor_borde)
    draw.ellipse(ojo_der, outline="white", width=grosor_borde)
    
    # Parpadeo real: doblando ojo desde arriba y abajo
    if parpado_ratio > 0:
        # Altura de “cerrado” parcial
        alto_ojo = ojo_izq[3] - ojo_izq[1]
        delta = int(alto_ojo * parpado_ratio / 2)
        # Párpado superior
        draw.rectangle((ojo_izq[0]+grosor_borde//2, ojo_izq[1],
                        ojo_izq[2]-grosor_borde//2, ojo_izq[1]+delta),
                        fill="black")
        draw.rectangle((ojo_der[0]+grosor_borde//2, ojo_der[1],
                        ojo_der[2]-grosor_borde//2, ojo_der[1]+delta),
                        fill="black")
        # Párpado inferior
        draw.rectangle((ojo_izq[0]+grosor_borde//2, ojo_izq[3]-delta,
                        ojo_izq[2]-grosor_borde//2, ojo_izq[3]),
                        fill="black")
        draw.rectangle((ojo_der[0]+grosor_borde//2, ojo_der[3]-delta,
                        ojo_der[2]-grosor_borde//2, ojo_der[3]),
                        fill="black")
    
    # Cejas moviéndose solo encima del ojo, sin cruzar
    ceja_y_base = ojo_izq[1] - margen_ceja
    ceja_altura = ceja_y_base + 20
    
    # Aplicar offset limitado: cejas no pueden entrar en ojo
    ceja_offset = min(ceja_offset, margen_ceja-5)
    ceja_y = ceja_y_base - ceja_offset
    ceja_altura_mod = ceja_altura - ceja_offset
    
    if emocion == "feliz":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura_mod), start=0, end=180, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura_mod), start=0, end=180, fill="white", width=5)
    elif emocion == "triste":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura_mod), start=180, end=360, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura_mod), start=180, end=360, fill="white", width=5)
    elif emocion == "sorprendido":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura_mod), start=0, end=180, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura_mod), start=0, end=180, fill="white", width=5)
    elif emocion == "enojado":
        draw.arc((ojo_izq[0], ceja_y, ojo_izq[2], ceja_altura_mod), start=180, end=360, fill="white", width=5)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura_mod), start=180, end=360, fill="white", width=5)
    elif emocion == "guiño":
        draw.line((ojo_izq[0], ojo_izq[3]-10, ojo_izq[2], ojo_izq[3]-10), fill="white", width=8)
        draw.arc((ojo_der[0], ceja_y, ojo_der[2], ceja_altura_mod), start=0, end=180, fill="white", width=5)
    
    display.image(img)

# Animación principal
while True:
    emocion_actual = random.choice(emociones)
    for ratio in [0.0, 0.2, 0.5, 0.8, 0.5, 0.2, 0.0]:  # parpadeo más real
        ceja_offset = random.randint(0, 10)  # movimiento natural, limitado
        dibujar_ojos_parpadeo_cejas(emocion_actual, parpado_ratio=ratio, ceja_offset=ceja_offset)
        time.sleep(0.15)
