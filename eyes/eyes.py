import board
import digitalio
from PIL import Image, ImageDraw
import adafruit_ili9341

# Pines
cs_pin = digitalio.DigitalInOut(board.D8)   # CS PIN 24
dc_pin = digitalio.DigitalInOut(board.D23)  # DC PIN 16
reset_pin = digitalio.DigitalInOut(board.D24) # RESET PIN 18

# Inicializar pantalla
display = adafruit_ili9341.ILI9341(
    board.SPI(),
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
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

# Mostrar imagen
display.image(image)
