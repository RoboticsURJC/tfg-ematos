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


# Ojo izquierdo tipo '-'
draw.line((80, 120, 150, 120), fill="white", width=8)  # Línea horizontal

# Ojo derecho tipo curva convexa hacia abajo ')'
draw.arc((180, 100, 250, 140), start=0, end=180, fill="white", width=8)  # Curva hacia abajo

display.image(img)