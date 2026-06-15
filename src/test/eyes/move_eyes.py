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

# Crear imagen nueva
img = Image.new("RGB", (240, 320), "black")
draw = ImageDraw.Draw(img)

# Texto
# draw.text((40, 150), "HOLIIIIIS", fill="white")

# Dibujar ojitos grandes y separados
# Ojo izquierdo
# draw.ellipse((30, 50, 110, 170), fill="white")   # Parte blanca
# draw.ellipse((65, 100, 85, 120), fill="black")   # Pupila

# # Ojo derecho
# draw.ellipse((130, 50, 210, 170), fill="white")  # Parte blanca
# draw.ellipse((165, 100, 185, 120), fill="black") # Pupila

# # Mostrar en pantalla
# display.image(img)


# Función para dibujar los ojos en una posición de pupila dada
def dibujar_ojos(pupila_offset_x):
    img = Image.new("RGB", (240, 320), "black")
    draw = ImageDraw.Draw(img)

    # Ojo izquierdo
    draw.ellipse((30, 50, 110, 170), fill="white")   # Parte blanca
    draw.ellipse((65 + pupila_offset_x, 100, 85 + pupila_offset_x, 120), fill="black")  # Pupila

    # Ojo derecho
    draw.ellipse((130, 50, 210, 170), fill="white")  # Parte blanca
    draw.ellipse((165 + pupila_offset_x, 100, 185 + pupila_offset_x, 120), fill="black") # Pupila

    display.image(img)

# Bucle para mover las pupilas de izquierda a derecha
while True:
    for offset in range(-10, 11, 2):  # De -10 a 10 px
        dibujar_ojos(offset)
        time.sleep(0.05)
    for offset in range(10, -11, -2): # De 10 a -10 px
        dibujar_ojos(offset)
        time.sleep(0.05)