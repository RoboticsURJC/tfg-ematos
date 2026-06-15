import pigpio
import time

IN1 = 5
IN2 = 6


# IN1 = 20
# IN2 = 21

pi = pigpio.pi()

if not pi.connected:
    print("No se pudo conectar a pigpio")
    exit()

# Configurar como salida
pi.set_mode(IN1, pigpio.OUTPUT)
pi.set_mode(IN2, pigpio.OUTPUT)

def motor_adelante(velocidad=128, tiempo=3):
    """
    velocidad: 0–255
    tiempo: segundos
    """
    pi.write(IN2, 0)                     # Dirección
    pi.set_PWM_dutycycle(IN1, velocidad) # PWM real
    time.sleep(tiempo)
    parar()

def motor_atras(velocidad=128, tiempo=3):
    pi.write(IN1, 0)
    pi.set_PWM_dutycycle(IN2, velocidad)
    time.sleep(tiempo)
    parar()

def parar():
    pi.set_PWM_dutycycle(IN1, 0)
    pi.set_PWM_dutycycle(IN2, 0)

try:
    print("Probando motor adelante...")
    motor_adelante(60, 3)

    time.sleep(1)

    print("Probando motor atrás...")
    motor_atras(60, 3)

finally:
    parar()
    pi.stop()