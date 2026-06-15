import cv2
import pickle
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2, Preview
from numpy.linalg import norm
import matplotlib.pyplot as plt
import pandas as pd

# Load TFLite model and allocate tensors for detection and recogniton.
try:
    detector = tflite.Interpreter(
        model_path="blaze_face_short_range.tflite",
        experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')]
    )

    recognizer = tflite.Interpreter(
        model_path="mobilefacenet.tflite",
        experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')]
    )
    print(" \n-------- Edge TPU detected and working -------- \n")
except Exception as e:
    print("Error at charging Edge TPU:", e)
    # face_detection_front
    detector = tflite.Interpreter(model_path="blaze_face_short_range.tflite")
    recognizer = tflite.Interpreter(model_path="mobilefacenet.tflite")

detector.allocate_tensors()
recognizer.allocate_tensors()


# Get input and output tensors.
input_details_detector = detector.get_input_details()
output_details_detector = detector.get_output_details()
input_shape_detector = input_details_detector[0]['shape']

input_details_recognizer = recognizer.get_input_details()
output_details_recognizer = recognizer.get_output_details()
input_shape_recognizer = input_details_recognizer[0]['shape']

picam2 = Picamera2()
picam2.preview_configuration.main.size =  (1280, 720)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

# load known faces embeddings
with open('known_faces_192.pkl', 'rb') as f:
    known_face_names, known_face_encodings = pickle.load(f)

known_faces_dict = {}
for name, encoding in zip(known_face_names, known_face_encodings):
   
    if name in known_faces_dict:
        known_faces_dict[name].append(encoding)
    else:
        known_faces_dict[name] = [encoding]

def cosine_similarity(a, b):
    return np.dot(a, b) 

def preprocess_face(face_img):
    img = cv2.resize(face_img, (input_shape_recognizer[2], input_shape_recognizer[1]))  # (width, height)
    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, axis=0)

def get_embedding(face_img):
    input_data = preprocess_face(face_img)
    recognizer.set_tensor(input_details_recognizer[0]['index'], input_data)
    recognizer.invoke()
    embedding = recognizer.get_tensor(output_details_recognizer[0]['index'])[0]
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def recognize_face(embedding, known_faces_dict, threshold=0.5):
    best_match = None
    best_score = -1
    for name, embeddings in known_faces_dict.items():
        for e in embeddings:
            score = cosine_similarity(embedding, e)
            #print(f"Compare with {name}: score = {score:.3f}")
            if score > best_score:
                best_score = score
                best_match = name
    if best_score > 0.75:
        return best_match, best_score
    elif best_score > 0.6:
        return "Desconocido (pero se parece a...)", best_score
    else:
        return None, best_score


def comparar_similitudes_emb_light(known_faces_dict, exportar_csv=False, umbral_parecido=0.6, mostrar_heatmap=False):
    nombres = list(known_faces_dict.keys())
    num_personas = len(nombres)
    matriz = np.zeros((num_personas, num_personas))

    for i in range(num_personas):
        for j in range(i, num_personas):
            if i == j:
                matriz[i][j] = 0.0
            else:
                embeddings_i = known_faces_dict[nombres[i]]
                embeddings_j = known_faces_dict[nombres[j]]

                distancias = [np.linalg.norm(e1 - e2) for e1 in embeddings_i for e2 in embeddings_j]
                promedio = np.mean(distancias)
                matriz[i][j] = matriz[j][i] = promedio

    df = pd.DataFrame(matriz, index=nombres, columns=nombres)

    if exportar_csv:
        df.to_csv("distancias_embeddings.csv")
        print("✅ CSV guardado como 'distancias_embeddings.csv'")

    print("\n🔗 Posibles personas parecidas (distancia < {:.2f}):".format(umbral_parecido))
    for i in range(num_personas):
        for j in range(i + 1, num_personas):
            if matriz[i][j] < umbral_parecido:
                print(f"✅ {nombres[i]} ↔ {nombres[j]} → distancia = {matriz[i][j]:.3f}")

    if mostrar_heatmap:
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            cax = ax.matshow(matriz, cmap="RdYlGn_r")
            plt.xticks(range(num_personas), nombres, rotation=90)
            plt.yticks(range(num_personas), nombres)
            plt.colorbar(cax, label="Distancia promedio")
            plt.title("Similitud entre personas (menos = más parecidos)")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print("No se pudo mostrar el heatmap:", e)

    return df


comparar_similitudes_emb_light(known_faces_dict, exportar_csv=True, umbral_parecido=0.5, mostrar_heatmap=False)

# print("\n--- Similitud entre embeddings conocidos ---")
# for i in range(len(known_face_encodings)):
#     for j in range(i+1, len(known_face_encodings)):
#         sim = cosine_similarity(known_face_encodings[i], known_face_encodings[j])
#         print(f"Similitud entre {known_face_names[i]} y {known_face_names[j]}: {sim:.4f}")

# while True:

#     frame = picam2.capture_array()
#     frame = cv2.flip(frame, 1)
#     h, w, _ = frame.shape

#     img_resized = cv2.resize(frame, (input_shape_detector[2], input_shape_detector[1]))

#     # Convert the image to numpy array
#     input_data = np.expand_dims(img_resized.astype(np.float32), axis=0)

#     # normalize 
#     input_data = input_data / 255.0

#     # Set the tensor to point to the input to be inferred 
#     detector.set_tensor(input_details_detector[0]['index'], input_data)

#     # run the inference
#     detector.invoke()

#     detections = detector.get_tensor(output_details_detector[0]['index'])[0]
#     confidences = detector.get_tensor(output_details_detector[1]['index'])[0]

   
    
#     for i in range(len(confidences)):
#         if confidences[i] > 0.75:
#             #print(f"Person Detect {i}")
          
#             ymin, xmin, ymax, xmax = detections[i][:4]
#             ymin, xmin = max(0, ymin), max(0, xmin)
#             ymax, xmax = min(1, ymax), min(1, xmax)
#             x1, y1 = int(xmin * w), int(ymin * h)
#             x2, y2 = int(xmax * w), int(ymax * h)

#             # Validar y ordenar coords
#             x1, x2 = sorted([x1, x2])
#             y1, y2 = sorted([y1, y2])

#             x1 = max(0, min(x1, w - 1))
#             x2 = max(0, min(x2, w - 1))
#             y1 = max(0, min(y1, h - 1))
#             y2 = max(0, min(y2, h - 1))

#             if (x2 - x1) < 10 or (y2 - y1) < 10:
#                 continue

#             # get face frame
#             face_img = frame[y1:y2, x1:x2]
#             #print(f"Face img shape: {face_img.shape}")

#             embedding = get_embedding(face_img)

#             person_name, score = recognize_face(embedding, known_faces_dict, threshold=0.75)
#             label = f"{person_name} ({score:.2f})" if person_name else "Unknown"
#             print(f"You are: {label}")
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             cv2.putText(frame, label, (x1, y1-10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                        
#     cv2.imshow("Recognition", frame)
#     if cv2.waitKey(1) == ord('q'):
#         break

# cv2.destroyAllWindows()
