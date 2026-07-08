

from gpiozero import Button
import time
import subprocess

BUTTON_PIN = 13
button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05)

click_times = []

# -----------------------------
# UTILIDADES
# -----------------------------

def is_ui_running():
    return subprocess.call(
        ["systemctl", "is-active", "--quiet", "robot-ui"]
    ) == 0


def start_stop_ui():
    if is_ui_running():
        print("Stopping UI")
        subprocess.run(["systemctl", "stop", "robot-ui"])
    else:
        print("Starting UI")
        subprocess.run(["systemctl", "start", "robot-ui"])


def reboot_system():
    print("Rebooting system")
    subprocess.run(["sudo", "reboot"])


# -----------------------------
# DETECCIÓN DE CLICK
# -----------------------------

def handle_click():
    global click_times

    now = time.time()
    click_times.append(now)

    # mantener solo clicks recientes
    click_times = [t for t in click_times if now - t < 0.6]

    # DOBLE CLICK → reboot
    if len(click_times) == 2:
        click_times = []
        reboot_system()
        return

    # CLICK SIMPLE → esperar a ver si hay segundo click
    if len(click_times) == 1:
        time.sleep(0.35)

        # si sigue siendo 1 → no hubo doble click
        if len(click_times) == 1:
            click_times = []
            start_stop_ui()


# -----------------------------
# EVENTO BOTÓN
# -----------------------------

button.when_pressed = handle_click

print("Botón activo")

while True:
    time.sleep(1)
