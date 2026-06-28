from gpiozero import RGBLED
from time import sleep
import sys

RED_PIN = 26
GREEN_PIN = 17
BLUE_PIN = 19

led = RGBLED(RED_PIN, GREEN_PIN, BLUE_PIN)

mode = sys.argv[1] if len(sys.argv) > 1 else "boot"

def blink(color, t=0.3):
    for _ in range(10):
        led.color = color
        sleep(t)
        led.color = (0, 0, 0)
        sleep(t)

try:
    if mode == "boot":
        # amarillo parpadeante
        blink((0.5, 0.15, 0))
        led.color(0, 1, 0)
        while True:
            sleep(1)

    elif mode == "ready":
        led.color = (0, 0.2, 0)  # verde fijo
        while True:
            sleep(1)

    elif mode == "shutdown":
        blink((1, 0, 0))  # rojo parpadeante

finally:
    led.color = (0, 0, 0)
    led.close()
