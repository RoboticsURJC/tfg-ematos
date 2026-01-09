import board
import digitalio
from PIL import Image, ImageDraw
import adafruit_ili9341

# SPI
spi = board.SPI()

# Pines según tu conexión
cs = digitalio.DigitalInOut(board.D8)
dc = digitalio.DigitalInOut(board.D23)
rst = digitalio.DigitalInOut(board.D24)

# Pantalla
display = adafruit_ili9341.ILI9341(
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    width=240,
    height=320,
    rotation=180
)

# Crear imagen
image = Image.new("RGB", (240, 320), "black")
draw = ImageDraw.Draw(image)

# Ojo izquierdo
draw.ellipse((40, 100, 120, 180), fill="white")
draw.ellipse((75, 135, 95, 155), fill="black")

# Ojo derecho
draw.ellipse((160, 100, 240, 180), fill="white")
draw.ellipse((195, 135, 215, 155), fill="black")

# Mostrar
display.image(image)
