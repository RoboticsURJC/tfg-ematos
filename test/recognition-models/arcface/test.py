import cv2
from deepface import DeepFace
import pickle
import numpy as np

# Cargar el clasificador y el codificador de etiquetas
with open("svm_classifier.pkl", "rb") as f:
    classifier = pickle.load(f)

with open("label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

# Función para predecir la persona
def predict_face(frame):
    # Extraer el embedding de la cara en el frame
    try:
        embedding = DeepFace.represent(frame, model_name="ArcFace")[0]["embedding"]
        # Hacer la predicción con el clasificador
        prediction = classifier.predict([embedding])
        predicted_label = label_encoder.inverse_transform(prediction)
        return predicted_label[0]
    except Exception as e:
        return "Error en la detección de la cara"

# Iniciar la cámara
cap = cv2.VideoCapture(0)  # 0 es el índice por defecto para la cámara interna

if not cap.isOpened():
    print("Error: No se puede acceder a la cámara.")
    exit()

while True:
    # Capturar frame por frame
    ret, frame = cap.read()

    if not ret:
        print("Error: No se pudo recibir el frame de la cámara.")
        break

    # Convertir el frame a escala de grises para mejorar el rendimiento (opcional)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detectar caras en el frame
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        # Dibujar un rectángulo alrededor de la cara detectada
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Extraer la región de interés (ROI) de la cara
        roi = frame[y:y + h, x:x + w]

        # Hacer la predicción sobre la cara detectada
        predicted_person = predict_face(roi)

        # Mostrar el nombre de la persona en el frame
        cv2.putText(frame, predicted_person, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Mostrar el frame con las predicciones en la pantalla
    cv2.imshow('Prediccion en tiempo real', frame)

    # Presionar 'q' para salir del bucle
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar las ventanas de OpenCV
cap.release()
cv2.destroyAllWindows()
