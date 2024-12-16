import cv2

# Init cam
cap = cv2.VideoCapture(0)

# Check camera
if not cap.isOpened():
    print("Camera unavailable.")
    exit()

while True:
    # Capture photograms
    ret, frame = cap.read()

    if not ret:
        print("No capture.")
        break

    # Mostrar el fotograma en una ventana
    cv2.imshow("Camera Test", frame)

    # Salir del bucle si se presiona la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()
