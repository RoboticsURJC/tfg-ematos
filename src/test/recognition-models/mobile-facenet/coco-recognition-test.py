import cv2
import numpy as np
import pickle
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2
from numpy.linalg import norm

# --- Carga modelo detector personas (Edge TPU) ---
person_detector = tflite.Interpreter(
    model_path="ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite",
    experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')]
)
person_detector.allocate_tensors()

input_details_person = person_detector.get_input_details()
output_details_person = person_detector.get_output_details()
input_shape_person = input_details_person[0]['shape']

# --- Carga modelo detector de caras BlazeFace (Edge TPU) ---
face_detector = tflite.Interpreter(
    model_path="face_detection_back.tflite",  # O front, según cámara
    experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')]
)
face_detector.allocate_tensors()

input_details_face = face_detector.get_input_details()
output_details_face = face_detector.get_output_details()
input_shape_face = input_details_face[0]['shape']

# --- Carga modelo de reconocimiento MobileFaceNet (Edge TPU) ---
recognizer = tflite.Interpreter(
    model_path="mobilefacenet.tflite",
    experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')]
)
recognizer.allocate_tensors()

input_details_recognizer = recognizer.get_input_details()
output_details_recognizer = recognizer.get_output_details()
input_shape_recognizer = input_details_recognizer[0]['shape']

# --- Carga embeddings conocidos ---
with open('known_faces_192.pkl', 'rb') as f:
    known_face_names, known_face_encodings = pickle.load(f)

known_faces_dict = {}
for name, encoding in zip(known_face_names, known_face_encodings):
    known_faces_dict.setdefault(name, []).append(encoding)

# --- Inicializa cámara ---
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (1280, 720), "format": "RGB888"}))
picam2.start()

# --- Funciones auxiliares ---
def cosine_similarity(a, b):
    return np.dot(a, b)

def preprocess_face(face_img):
    img = cv2.resize(face_img, (input_shape_recognizer[2], input_shape_recognizer[1]))  # width, height
    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, axis=0)

def get_embedding(face_img):
    input_data = preprocess_face(face_img)
    recognizer.set_tensor(input_details_recognizer[0]['index'], input_data)
    recognizer.invoke()
    embedding = recognizer.get_tensor(output_details_recognizer[0]['index'])[0]
    return embedding / np.linalg.norm(embedding)

def recognize_face(embedding, known_faces_dict, threshold, margin):
    scored_matches = []
    for name, embeddings in known_faces_dict.items():
        for e in embeddings:
            score = cosine_similarity(embedding, e)
            scored_matches.append((name, score))
    if not scored_matches:
        return None, -1
    scored_matches.sort(key=lambda x: x[1], reverse=True)
    best_name, best_score = scored_matches[0]
    second_score = scored_matches[1][1] if len(scored_matches) > 1 else -1
    if best_score >= threshold and (best_score - second_score) > margin:
        return best_name, best_score
    else:
        return None, best_score

def nothing(x):
    pass

# --- Interfaz para ajustar threshold y margin ---
cv2.namedWindow("Recognition")
cv2.createTrackbar('Threshold', 'Recognition', 75, 100, nothing)
cv2.createTrackbar('Margin', 'Recognition', 5, 100, nothing)

while True:
    thresh_slider = cv2.getTrackbarPos('Threshold', 'Recognition') / 100.0
    margin_slider = cv2.getTrackbarPos('Margin', 'Recognition') / 100.0

    frame = picam2.capture_array()
    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # --- Detectar personas ---
    # Prepara imagen para detector persona
    img_person = cv2.resize(rgb_frame, (input_shape_person[2], input_shape_person[1]))
    if input_details_person[0]['dtype'] == np.float32:
        img_person = img_person.astype(np.float32) / 255.0
    else:
        img_person = img_person.astype(np.uint8)
    input_data_person = np.expand_dims(img_person, axis=0)
    person_detector.set_tensor(input_details_person[0]['index'], input_data_person)
    person_detector.invoke()

    boxes_person = person_detector.get_tensor(output_details_person[0]['index'])[0]
    classes_person = person_detector.get_tensor(output_details_person[1]['index'])[0]
    scores_person = person_detector.get_tensor(output_details_person[2]['index'])[0]

    for i in range(len(scores_person)):
        if scores_person[i] > 0.6 and classes_person[i] == 0:  # clase 0 = persona
            ymin, xmin, ymax, xmax = boxes_person[i]
            x1, y1 = int(xmin * width), int(ymin * height)
            x2, y2 = int(xmax * width), int(ymax * height)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            # --- Detectar caras dentro del bounding box persona ---
            person_roi = frame[y1:y2, x1:x2]
            if person_roi.size == 0:
                continue

            face_input = cv2.resize(person_roi, (input_shape_face[2], input_shape_face[1]))
            face_input = face_input.astype(np.float32) / 255.0
            face_input = np.expand_dims(face_input, axis=0)

            face_detector.set_tensor(input_details_face[0]['index'], face_input)
            face_detector.invoke()

            face_boxes = face_detector.get_tensor(output_details_face[0]['index'])[0]
            face_scores = face_detector.get_tensor(output_details_face[1]['index'])[0]

            for j in range(len(face_scores)):
                if face_scores[j] > 0.75:
                    fymin, fxmin, fymax, fxmax = face_boxes[j][:4]

                    fx1 = int(fxmin * (x2 - x1)) + x1
                    fy1 = int(fymin * (y2 - y1)) + y1
                    fx2 = int(fxmax * (x2 - x1)) + x1
                    fy2 = int(fymax * (y2 - y1)) + y1

                    fx1, fx2 = sorted([max(0, fx1), min(fx2, width - 1)])
                    fy1, fy2 = sorted([max(0, fy1), min(fy2, height - 1)])

                    face_img = frame[fy1:fy2, fx1:fx2]
                    if face_img.size == 0:
                        continue

                    # --- Reconocer cara ---
                    embedding = get_embedding(face_img)
                    person_name, score = recognize_face(embedding, known_faces_dict, threshold=thresh_slider, margin=margin_slider)

                    label = f"{person_name} ({score:.2f})" if person_name else "Unknown"
                    print(f"Name: {label}")

                    cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (fx1, fy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
