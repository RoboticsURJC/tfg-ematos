from gpiozero import Button
import subprocess
import time

BUTTON_PIN = 13
button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05)

click_times = []

def shutdown():
    print("Apagando Raspberry...")
    subprocess.run(["sudo", "shutdown", "-h", "now"])

def reboot():
    print("Reiniciando Raspberry...")
    subprocess.run(["sudo", "reboot"])

def handle_click():
    global click_times

    now = time.time()
    click_times.append(now)

    # mantener solo clicks recientes
    click_times = [t for t in click_times if now - t < 0.6]

    # doble click → reboot
    if len(click_times) == 2:
        click_times = []
        reboot()
        return

    # click simple → esperar confirmación
    if len(click_times) == 1:
        time.sleep(0.4)

        if len(click_times) == 1:
            click_times = []
            shutdown()

button.when_pressed = handle_click

print("Botón activo")

while True:
    time.sleep(1)
