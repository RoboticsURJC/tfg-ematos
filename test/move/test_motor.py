import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

IN1 = 20
IN2 = 21

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

# Pines de 1000 Hz
pwm1 = GPIO.PWM(IN1, 1000)
# pwm2 = GPIO.PWM(IN2, 1000)

pwm1.start(0)
# pwm2.start(0)

try:


    
    time.sleep(10)

    print("Motor adelante")
    pwm1.ChangeDutyCycle(20)
    # pwm1.ChangeDutyCycle()
    time.sleep(3)

    print("Motor más rápido")
    pwm1.ChangeDutyCycle(60)
    # pwm1.ChangeDutyCycle()
    time.sleep(3)

    print("Motor parar")
    pwm1.ChangeDutyCycle(0)
    # pwm1.ChangeDutyCycle()

finally:
    GPIO.cleanup()
