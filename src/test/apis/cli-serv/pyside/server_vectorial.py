import os
import base64
import pickle
import shutil
import tempfile
import cv2
import numpy as np
import face_recognition
import hnswlib
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# =====================
# Configuración inicial
# =====================

curr_dir = os.path.dirname(__file__)
data_path = os.path.join(curr_dir, "..", "..", "known_faces.pkl")
people_path = os.path.join(curr_dir, "..", "..", "known_persons")
index_path = os.path.join(curr_dir, "..", "..", "hnsw_index.bin")

os.makedirs(people_path, exist_ok=True)

DIM = 128  # tamaño del vector de face_recognition (128)


# =====================
# Funciones auxiliares
# =====================

def log(msg, color="\033[96m"):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{now}] {msg}\033[0m")


def load_known_faces():
    if os.path.exists(data_path):
        with open(data_path, "rb") as f:
            return pickle.load(f)
    return [], []


def save_known_faces(names, encodings):
    tmp = tempfile.mktemp()
    with open(tmp, "wb") as f:
        pickle.dump((names, encodings), f)
    shutil.move(tmp, data_path)


# =====================
# Inicializar Base de Datos
# =====================

known_face_names, known_face_encodings = load_known_faces()

index = hnswlib.Index(space='l2', dim=DIM)

if len(known_face_encodings) > 0:
    log(f"Cargando {len(known_face_encodings)} encodings al índice HNSW...", "\033[92m")
    index.init_index(max_elements=20000, ef_construction=200, M=16)
    index.add_items(np.array(known_face_encodings), np.arange(len(known_face_encodings)))
else:
    log("Inicializando índice vacío...", "\033[93m")
    index.init_index(max_elements=20000, ef_construction=200, M=16)

index.set_ef(50)  # precisión de búsqueda


# =====================
# Rutas del servidor
# =====================

@app.route("/recognize", methods=["POST"])
def recognize():
    log("Petición de reconocimiento recibida.", "\033[96m")

    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "Falta la imagen"}), 400

    # Decodificar imagen
    try:
        image_data = base64.b64decode(data["image"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except:
        return jsonify({"error": "Error al decodificar la imagen"}), 400

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        return jsonify({
            "recognized": [],
            "message": "No se detectó ningún rostro"
        })

    results = []

    for encoding in face_encodings:
        # Búsqueda rápida en HNSW
        labels, distances = index.knn_query(np.array([encoding]), k=1)
        idx = labels[0][0]
        dist = distances[0][0]

        # Umbral recomendado
        if dist < 0.55:
            name = known_face_names[idx]
        else:
            name = "Desconocido"

        results.append(name)

    return jsonify({
        "recognized": results,
        "message": f"Reconocidos: {', '.join(results)}"
    })


@app.route("/register", methods=["POST"])
def register():
    log("Petición de registro recibida.", "\033[96m")

    data = request.get_json()
    if not data or "name" not in data or "images" not in data:
        return jsonify({"error": "Faltan campos requeridos"}), 400

    name = data["name"].strip()
    images = data["images"]

    if not name:
        return jsonify({"error": "El nombre no puede estar vacío"}), 400

    person_dir = os.path.join(people_path, name)
    os.makedirs(person_dir, exist_ok=True)

    new_encodings = []

    for i, img_b64 in enumerate(images):
        try:
            img_data = base64.b64decode(img_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except:
            continue

        encs = face_recognition.face_encodings(rgb_frame)
        if encs:
            new_encodings.append(encs[0])
            cv2.imwrite(os.path.join(person_dir, f"{name}_{i+1}.jpg"), frame)

    if not new_encodings:
        return jsonify({"status": "error", "message": "No se detectaron rostros válidos"})

    # Guardar en memoria
    for enc in new_encodings:
        known_face_encodings.append(enc)
        known_face_names.append(name)

        new_id = len(known_face_encodings) - 1
        index.add_items(np.array([enc]), np.array([new_id]))

    # Guardar en disco
    save_known_faces(known_face_names, known_face_encodings)
    index.save_index(index_path)

    log(f"'{name}' registrado con {len(new_encodings)} imágenes.", "\033[92m")

    return jsonify({
        "status": "ok",
        "message": f"{name} registrado con {len(new_encodings)} imágenes válidas"
    })


# =====================
# Run
# =====================
if __name__ == "__main__":
    log("Servidor Flask en http://0.0.0.0:5000", "\033[92m")
    app.run(host="0.0.0.0", port=5000)
