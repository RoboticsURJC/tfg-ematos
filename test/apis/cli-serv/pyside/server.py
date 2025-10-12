# server.py — versión mejorada
import os
import base64
import pickle
import shutil
import tempfile
import cv2
import numpy as np
import face_recognition
from flask import Flask, request, jsonify

app = Flask(__name__)

# =====================
# Configuración inicial
# =====================

DATA_PATH = "known_faces.pkl"
PEOPLE_DIR = "known_persons"
os.makedirs(PEOPLE_DIR, exist_ok=True)


# =====================
# Funciones auxiliares
# =====================

def load_known_faces():
    """Carga los rostros conocidos desde el archivo pickle."""
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "rb") as f:
            return pickle.load(f)
    return [], []


def save_known_faces(names, encodings):
    """Guarda los rostros conocidos de forma segura."""
    tmp = tempfile.mktemp()
    with open(tmp, "wb") as f:
        pickle.dump((names, encodings), f)
    shutil.move(tmp, DATA_PATH)


# =====================
# Cargar base de datos
# =====================

known_face_names, known_face_encodings = load_known_faces()


# =====================
# Rutas del servidor
# =====================

@app.route("/recognize", methods=["POST"])
def recognize():
    """Reconocer un rostro en una imagen enviada por el cliente."""
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "Falta la imagen"}), 400

    try:
        image_data = base64.b64decode(data["image"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        return jsonify({"error": "Error al decodificar imagen"}), 400

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        return jsonify({"recognized": [], "message": "No se detectó ningún rostro"})

    results = []
    for encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, encoding)
        name = "Desconocido"
        face_distances = face_recognition.face_distance(known_face_encodings, encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
        results.append(name)

    return jsonify({
        "recognized": results,
        "message": f"Reconocidos: {', '.join(results)}"
    })


@app.route("/register", methods=["POST"])
def register():
    """Registrar un nuevo usuario con varias imágenes."""
    data = request.get_json()
    if not data or "name" not in data or "images" not in data:
        return jsonify({"error": "Faltan campos requeridos"}), 400

    name = data["name"].strip()
    images = data["images"]

    if not name:
        return jsonify({"error": "El nombre no puede estar vacío"}), 400

    person_dir = os.path.join(PEOPLE_DIR, name)
    os.makedirs(person_dir, exist_ok=True)

    new_encodings = []

    for i, img_b64 in enumerate(images):
        try:
            img_data = base64.b64decode(img_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except Exception:
            continue

        face_encs = face_recognition.face_encodings(rgb_frame)
        if face_encs:
            new_encodings.append(face_encs[0])
            cv2.imwrite(os.path.join(person_dir, f"{name}_{i+1}.jpg"), frame)

    if not new_encodings:
        return jsonify({"status": "error", "message": "No se detectaron rostros válidos"})

    known_face_names.extend([name] * len(new_encodings))
    known_face_encodings.extend(new_encodings)
    save_known_faces(known_face_names, known_face_encodings)

    return jsonify({
        "status": "ok",
        "message": f"{name} registrado con {len(new_encodings)} imágenes válidas"
    })


# =====================
# Run
# =====================
if __name__ == "__main__":
    print("Server running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
