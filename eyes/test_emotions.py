import random
import time
import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw

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


# lista de emociones
emociones = ["feliz", "triste", "sorprendido", "guiño", "enojado"]

# def dibujar_ojos(emocion, pupila_offset_x=0, pupila_offset_y=0):
    
#     # Crear imagen nueva
#     img = Image.new("RGB", (240, 320), "black")
#     draw = ImageDraw.Draw(img)
    
    
#     # Ojo izquierdo
#     if emocion == "feliz":
#         draw.line((60, 120, 100, 120), fill="white", width=6)
#         left_pup_x = 80 + pupila_offset_x
#         left_pup_y = 120 + pupila_offset_y
#     elif emocion == "triste":
#         draw.line((60, 140, 100, 120), fill="white", width=6)
#         left_pup_x = 80 + pupila_offset_x
#         left_pup_y = 130 + pupila_offset_y
#     elif emocion == "sorprendido":
#         draw.ellipse((60, 100, 100, 140), fill="white")
#         left_pup_x = 80 + pupila_offset_x
#         left_pup_y = 120 + pupila_offset_y
#     elif emocion == "guiño":
#         draw.line((60, 120, 100, 120), fill="white", width=6)
#         left_pup_x = 80 + pupila_offset_x
#         left_pup_y = 120 + pupila_offset_y
#     elif emocion == "enojado":
#         draw.line((60, 140, 100, 120), fill="white", width=6)
#         left_pup_x = 80 + pupila_offset_x
#         left_pup_y = 125 + pupila_offset_y
    
#     # Pupila izquierda
#     draw.ellipse((left_pup_x-5, left_pup_y-5, left_pup_x+5, left_pup_y+5), fill="black")
    
#     # Ojo derecho
#     if emocion == "feliz":
#         draw.arc((140, 100, 200, 160), start=0, end=180, fill="white", width=6)
#         right_pup_x = 165 + pupila_offset_x
#         right_pup_y = 120 + pupila_offset_y
#     elif emocion == "triste":
#         draw.arc((140, 100, 200, 160), start=180, end=360, fill="white", width=6)
#         right_pup_x = 165 + pupila_offset_x
#         right_pup_y = 130 + pupila_offset_y
#     elif emocion == "sorprendido":
#         draw.ellipse((140, 100, 180, 140), fill="white")
#         right_pup_x = 160 + pupila_offset_x
#         right_pup_y = 120 + pupila_offset_y
#     elif emocion == "guiño":
#         draw.arc((140, 100, 200, 160), start=20, end=160, fill="white", width=6)
#         right_pup_x = 160 + pupila_offset_x
#         right_pup_y = 120 + pupila_offset_y
#     elif emocion == "enojado":
#         draw.arc((140, 100, 200, 160), start=-20, end=160, fill="white", width=6)
#         right_pup_x = 160 + pupila_offset_x
#         right_pup_y = 125 + pupila_offset_y
    
#     # Pupila derecha
#     draw.ellipse((right_pup_x-5, right_pup_y-5, right_pup_x+5, right_pup_y+5), fill="black")
    
#     display.image(img)

# # Animación principal
# while True:
#     emocion_actual = random.choice(emociones)  # Cambia de emoción
#     for offset in range(-5, 6, 1):  # Pupilas que se mueven
#         dibujar_ojos(emocion_actual, pupila_offset_x=offset)
#         time.sleep(0.05)
#     for offset in range(5, -6, -1):
#         dibujar_ojos(emocion_actual, pupila_offset_x=offset)
#         time.sleep(0.05)


# def dibujar_ojos_con_cejas(emocion, pupila_offset_x=0, pupila_offset_y=0):
#     img = Image.new("RGB", (240, 320), "black")
#     draw = ImageDraw.Draw(img)
    
#     # Ojo izquierdo
#     draw.ellipse((50, 100, 110, 160), fill="white")  # Parte blanca
#     draw.ellipse((75 + pupila_offset_x, 125 + pupila_offset_y, 95 + pupila_offset_x, 145 + pupila_offset_y), fill="black")  # Pupila

#     # Ojo derecho
#     draw.ellipse((130, 100, 190, 160), fill="white")
#     draw.ellipse((155 + pupila_offset_x, 125 + pupila_offset_y, 175 + pupila_offset_x, 145 + pupila_offset_y), fill="black")

#     # Cejas según emoción
#     if emocion == "feliz":
#         # Cejas levantadas suavemente
#         draw.line((50, 90, 110, 95), fill="white", width=4)  # Izquierda
#         draw.line((130, 95, 190, 90), fill="white", width=4) # Derecha
#     elif emocion == "triste":
#         # Cejas inclinadas hacia arriba en el centro
#         draw.line((50, 95, 110, 90), fill="white", width=4)  # Izquierda
#         draw.line((130, 90, 190, 95), fill="white", width=4) # Derecha
#     elif emocion == "sorprendido":
#         # Cejas rectas y arriba
#         draw.line((50, 85, 110, 85), fill="white", width=4)  # Izquierda
#         draw.line((130, 85, 190, 85), fill="white", width=4) # Derecha
#     elif emocion == "enojado":
#         # Cejas inclinadas hacia abajo en el centro
#         draw.line((50, 95, 110, 90), fill="white", width=4)  # Izquierda
#         draw.line((130, 90, 190, 95), fill="white", width=4) # Derecha
#     elif emocion == "guiño":
#         # Ojo izquierdo cerrado tipo guiño
#         draw.line((50, 130, 110, 130), fill="white", width=6)  # Línea horizontal ojo cerrado
#         # Ojo derecho ceja levantada
#         draw.line((130, 90, 190, 85), fill="white", width=4)  

#     display.image(img)

# # Animación principal
# while True:
#     emocion_actual = random.choice(emociones)
#     for offset in range(-5, 6, 1):
#         dibujar_ojos_con_cejas(emocion_actual, pupila_offset_x=offset)
#         time.sleep(0.05)
#     for offset in range(5, -6, -1):
#         dibujar_ojos_con_cejas(emocion_actual, pupila_offset_x=offset)
#         time.sleep(0.05)


def dibujar_ojos_con_cejas_parpados(emocion, pupila_offset_x=0, pupila_offset_y=0, parpado_ratio=0.0):
    """
    parpado_ratio: 0.0 = ojo abierto, 1.0 = ojo cerrado
    """
    img = Image.new("RGB", (240, 320), "black")
    draw = ImageDraw.Draw(img)
    
    
    # Ojo izquierdo
    draw.ellipse((50, 100, 110, 160), fill="white")
    draw.ellipse((75 + pupila_offset_x, 125 + pupila_offset_y, 95 + pupila_offset_x, 145 + pupila_offset_y), fill="black")
    
    # Ojo derecho
    draw.ellipse((130, 100, 190, 160), fill="white")
    draw.ellipse((155 + pupila_offset_x, 125 + pupila_offset_y, 175 + pupila_offset_x, 145 + pupila_offset_y), fill="black")
    
    # Párpados
    parpado_alto = int(100 + 60 * parpado_ratio / 2)  # arriba del ojo
    parpado_bajo = int(160 - 60 * parpado_ratio / 2)  # abajo del ojo
    draw.rectangle((50, 100, 110, parpado_alto), fill="black")  # párpado superior izquierdo
    draw.rectangle((50, parpado_bajo, 110, 160), fill="black")  # párpado inferior izquierdo
    draw.rectangle((130, 100, 190, parpado_alto), fill="black")  # párpado superior derecho
    draw.rectangle((130, parpado_bajo, 190, 160), fill="black")  # párpado inferior derecho
    
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

# Animación principal con parpadeo
while True:
    emocion_actual = random.choice(emociones)
    # Pupilas que se mueven de lado a lado
    for offset in range(-5, 6, 1):
        # Parpadeo aleatorio
        parpado_ratio = random.choice([0.0, 0.0, 0.0, 0.5, 1.0])  # ojos abiertos la mayoría del tiempo, parpadeo ocasional
        dibujar_ojos_con_cejas_parpados(emocion_actual, pupila_offset_x=offset, parpado_ratio=parpado_ratio)
        time.sleep(0.1)
    for offset in range(5, -6, -1):
        parpado_ratio = random.choice([0.0, 0.0, 0.0, 0.5, 1.0])
        dibujar_ojos_con_cejas_parpados(emocion_actual, pupila_offset_x=offset, parpado_ratio=parpado_ratio)
        time.sleep(0.1)