from ultralytics import YOLO
import cv2

# Cargar el modelo entrenado
model = YOLO("best-1.pt")  # Asegúrate de que este archivo existe

# Iniciar captura de video (0 = cámara web)
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Realizar detección con YOLO
    results = model(frame)  

    # Dibujar los resultados en la imagen
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordenadas del bounding box
            conf = box.conf[0].item()  # Confianza
            cls = int(box.cls[0].item())  # Clase detectada

            # Dibujar caja y etiqueta
            label = f"{model.names[cls]} {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Mostrar imagen en tiempo real
    cv2.imshow("YOLOv11 Detection", frame)

    # Presiona 'q' para salir
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
