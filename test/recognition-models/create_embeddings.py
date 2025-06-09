import os
import cv2
import numpy as np
import pickle
import tflite_runtime.interpreter as tflite
from numpy.linalg import norm
import imghdr
import magic  # Para detección más precisa de tipos MIME

# Configuración
MODEL_PATH = "mobilefacenet.tflite"
KNOWN_PERSONS_FOLDER = "known_persons"
OUTPUT_PKL = "known_faces_192.pkl"

# Carga el modelo TFLite
try:
    interpreter = tflite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
except Exception as e:
    raise RuntimeError(f"Error al cargar el modelo TFLite: {str(e)}")

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape']

def is_image_file(filepath):
    """Verifica si el archivo es una imagen válida usando múltiples métodos"""
    # Método 1: Verificación de firma de archivo (más confiable)
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(filepath)
    if file_type not in ['image/jpeg', 'image/png']:
        return False
    
    # Método 2: Verificación con imghdr (complementario)
    image_type = imghdr.what(filepath)
    if image_type not in ['jpeg', 'jpg', 'png']:
        return False
    
    return True

def preprocess_face(face_img):
    """Preprocesamiento de la imagen facial"""
    try:
        img = cv2.resize(face_img, (input_shape[2], input_shape[1]))
        return np.expand_dims(img.astype(np.float32) / 255.0, axis=0)
    except Exception as e:
        raise RuntimeError(f"Error en preprocesamiento: {str(e)}")

def get_embedding(face_img):
    """Obtiene el embedding facial"""
    try:
        input_data = preprocess_face(face_img)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        embedding = interpreter.get_tensor(output_details[0]['index'])[0]
        return embedding / norm(embedding)
    except Exception as e:
        raise RuntimeError(f"Error al generar embedding: {str(e)}")

def load_and_encode_faces(folder_path):
    """Carga y codifica todas las caras conocidas"""
    known_face_names = []
    known_face_encodings = []
    
    for person_name in os.listdir(folder_path):
        person_folder = os.path.join(folder_path, person_name)
        if not os.path.isdir(person_folder):
            continue
            
        for img_name in os.listdir(person_folder):
            img_path = os.path.join(person_folder, img_name)
            
            # Verificación robusta del tipo de archivo
            if not is_image_file(img_path):
                print(f"[!] Archivo ignorado (no es imagen válida): {img_path}")
                continue
                
            try:
                img = cv2.imread(img_path)
                if img is None:
                    raise ValueError("OpenCV no pudo leer la imagen")
                
                embedding = get_embedding(img)
                known_face_names.append(person_name)
                known_face_encodings.append(embedding)
                print(f"[+] Procesado: {person_name} - {img_name}")
                
            except Exception as e:
                print(f"[!] Error procesando {img_path}: {str(e)}")
                continue
                
    return known_face_names, known_face_encodings

if __name__ == "__main__":
    print("=== Sistema de generación de embeddings ===")
    print(f"Dimensión de embeddings: {output_details[0]['shape']}")
    
    try:
        names, encodings = load_and_encode_faces(KNOWN_PERSONS_FOLDER)
        
        if not names:
            raise ValueError("No se encontraron imágenes válidas para procesar")
            
        with open(OUTPUT_PKL, "wb") as f:
            pickle.dump((names, encodings), f)
            
        print(f"\n✔️ Embeddings guardados en '{OUTPUT_PKL}'")
        print(f"Total de caras procesadas: {len(names)}")
        
    except Exception as e:
        print(f"\n❌ Error crítico: {str(e)}")
        exit(1)
