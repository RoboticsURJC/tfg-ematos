import os
import cv2
import numpy as np
import pickle
import tflite_runtime.interpreter as tflite
from numpy.linalg import norm

# Configura la ruta a tu modelo y la carpeta de imágenes conocidas
MODEL_PATH = "mobilefacenet.tflite"
KNOWN_PERSONS_FOLDER = "/home/elisa/tfg-ematos/test/recognition-models/face-recognition/known_persons"
OUTPUT_PKL = "known_faces_192.pkl"

# Carga el modelo TFLite
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape']  # normalmente [1, w, h, 3]

def preprocess_face(face_img):
    # Redimensiona y normaliza (ajusta según tu modelo)
    img = cv2.resize(face_img, (input_shape[2], input_shape[1]))
    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, axis=0)

def get_embedding(face_img):
    input_data = preprocess_face(face_img)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    embedding = interpreter.get_tensor(output_details[0]['index'])[0]
    embedding = embedding / norm(embedding)  # Normalizar vector
    return embedding

def load_and_encode_faces(folder_path):
    known_face_names = []
    known_face_encodings = []
    for person_name in os.listdir(folder_path):
        person_folder = os.path.join(folder_path, person_name)
        if not os.path.isdir(person_folder):
            continue
        for img_name in os.listdir(person_folder):
            if not (img_name.endswith(".jpg") or img_name.endswith(".png")):
                continue
            img_path = os.path.join(person_folder, img_name)
            img = cv2.imread(img_path)
            if img is None:
                print(f"No se pudo cargar la imagen: {img_path}")
                continue
            
            # Aquí asumo que la cara ocupa toda la imagen o que la imagen está recortada a la cara
            # Si no, deberías detectar y recortar la cara primero
            embedding = get_embedding(img)
            
            known_face_names.append(person_name)
            known_face_encodings.append(embedding)
            print(f"Procesado: {person_name} - {img_name}")
    return known_face_names, known_face_encodings

if __name__ == "__main__":
    print("Generando embeddings con dimensiones:", output_details[0]['shape'])
    names, encodings = load_and_encode_faces(KNOWN_PERSONS_FOLDER)

    # Guardar embeddings y nombres
    with open(OUTPUT_PKL, "wb") as f:
        pickle.dump((names, encodings), f)

    print(f"Embeddings guardados en '{OUTPUT_PKL}'")
