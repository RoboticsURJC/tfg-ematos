import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

IN1 = 20
IN2 = 21

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

try:
    time.sleep(10)

    print("Motor adelante")
    GPIO.output(IN1, 1)
    GPIO.output(IN2, 0)
    time.sleep(3)

    print("Motor atrás")
    GPIO.output(IN1, 0)
    GPIO.output(IN2, 1)
    time.sleep(3)

    print("Motor parar")
    GPIO.output(IN1, 0)
    GPIO.output(IN2, 0)

finally:
    GPIO.cleanup()
