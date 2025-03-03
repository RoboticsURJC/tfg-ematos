from ultralytics import YOLO
import cv2

# Cargar el modelo entrenado
model = YOLO("best-4.pt")  # Asegúrate de que este archivo existe

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml") 


def detect_bounding_box(frame):
    gray_image = cv2.cvtColor(viframed, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_image, 1.1, 5, minSize=(40, 40))
    for (x, y, w, h) in faces:
        roi_gray = gray_image[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray)

        if (len(eyes) == 2):
          print(len(eyes))
          cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 4)
          cv2.putText(frame, "Unknown Person", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

          for (ex,ey,ew,eh) in eyes:
              cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,127,255),2)

    return faces


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

            if conf < 0.2:
                faces = detect_bounding_box(frame)

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
