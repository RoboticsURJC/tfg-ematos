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
import time
from datetime import datetime

app = Flask(__name__)

# =====================
# Configuración inicial
# =====================

# DATA_PATH = "/home/elisa/uni/tfg-ematos/test/apis/cli-serv/known_faces.pkl"
# PEOPLE_DIR = "/home/elisa/uni/tfg-ematos/test/apis/known_persons"

curr_dir = os.path.dirname(__file__)
data_path = os.path.join(curr_dir, "..", "..", "known_faces.pkl")
people_path = os.path.join(curr_dir, "..", "..", "known_persons")


os.makedirs(people_path, exist_ok=True)


# =====================
# Funciones auxiliares
# =====================

def log(msg, color="\033[96m"):  # cian por defecto
    """Imprime mensajes con color y timestamp."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{now}] {msg}\033[0m")
    

def load_known_faces():
    """Carga los rostros conocidos desde el archivo pickle."""
    if os.path.exists(data_path):
        with open(data_path, "rb") as f:
            return pickle.load(f)
    return [], []


def save_known_faces(names, encodings):
    """Guarda los rostros conocidos de forma segura."""
    tmp = tempfile.mktemp()
    with open(tmp, "wb") as f:
        pickle.dump((names, encodings), f)
    shutil.move(tmp, data_path)


# =====================
# Cargar base de datos
# =====================

known_face_names, known_face_encodings = load_known_faces()


# =====================
# Rutas del servidor
# =====================

@app.route("/recognize", methods=["POST"])
def recognize():
        
    # Reconocer un rostro en una imagen enviada por el cliente.
    
    log("Recibida petición de reconocimiento facial.", "\033[96m")
    
    data = request.get_json()
    if not data or "image" not in data:
        log("Error: falta campo 'image' en la solicitud.", "\033[91m")
        return jsonify({"error": "Falta la imagen"}), 400

    try:
        image_data = base64.b64decode(data["image"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        log("Error al decodificar la imagen recibida.", "\033[93m")
        return jsonify({"error": "Error al decodificar imagen"}), 400

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        log("No se detectó ningún rostro en la imagen.", "\033[93m")
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
    
    # Registrar un nuevo usuario con varias imágenes.
    
    log("Recibida petición de registro de nuevo usuario.", "\033[96m")
    
    data = request.get_json()
    if not data or "name" not in data or "images" not in data:
        log("Error: faltan campos requeridos (name/images).", "\033[91m")
        return jsonify({"error": "Faltan campos requeridos"}), 400

    name = data["name"].strip()
    images = data["images"]

    if not name:
        log("Error: nombre vacío en el registro.", "\033[93m")
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
        except Exception:
            continue

        face_encs = face_recognition.face_encodings(rgb_frame)
        if face_encs:
            new_encodings.append(face_encs[0])
            cv2.imwrite(os.path.join(person_dir, f"{name}_{i+1}.jpg"), frame)

    if not new_encodings:
        log("❌ No se detectaron rostros válidos en las imágenes.", "\033[91m")         
        return jsonify({"status": "error", "message": "No se detectaron rostros válidos"})

    known_face_names.extend([name] * len(new_encodings))
    known_face_encodings.extend(new_encodings)
    save_known_faces(known_face_names, known_face_encodings)

    log(f"Usuario '{name}' registrado con {len(new_encodings)} imágenes válidas.", "\033[92m")

    
    return jsonify({
        "status": "ok",
        "message": f"{name} registrado con {len(new_encodings)} imágenes válidas"
    })



# =====================
# Run
# =====================
if __name__ == "__main__":
    log("Iniciando servidor Flask en http://0.0.0.0:5000", "\033[92m")
    app.run(host="0.0.0.0", port=5000)
