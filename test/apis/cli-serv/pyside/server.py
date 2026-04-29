# server.py 
import os
import base64
import pickle
import shutil
import tempfile
import cv2
import logging
import numpy as np
import face_recognition
from flask import Flask, request, jsonify
import time
from datetime import datetime


# ==========================================================
# 🔧 CONFIGURACIÓN LOGGER
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger("FaceServer")
app = Flask(__name__)

# =====================
# Configuración inicial
# =====================

# DATA_PATH = "/home/elisa/uni/tfg-ematos/test/apis/cli-serv/known_faces.pkl"
# PEOPLE_DIR = "/home/elisa/uni/tfg-ematos/test/apis/known_persons"


# ==========================================================
#  RUTAS DEL SISTEMA
# ==========================================================
curr_dir = os.path.dirname(__file__)
data_path = os.path.join(curr_dir, "..", "..", "known_faces.pkl")

## @brief Carpeta donde se guardan imágenes de usuarios
people_path = os.path.join(curr_dir, "..", "..", "known_persons")


os.makedirs(people_path, exist_ok=True)



def log(msg, color="\033[96m"):  # cian por defecto
    """Imprime mensajes con color y timestamp."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{now}] {msg}\033[0m")
    


# ==========================================================
# CARGA / GUARDADO DE BASE DE DATOS
# ==========================================================

def load_known_faces():
    """
    @brief Carga embeddings faciales desde disco.

    @return tuple (names, encodings)
    """
    
    if os.path.exists(data_path):
        with open(data_path, "rb") as f:
            logger.info("Base de datos facial cargada correctamente")
            return pickle.load(f)
        
    logger.warning("No existe base de datos previa. Inicializando vacía.")
    return [], []


def save_known_faces(names, encodings):
    """
    @brief Guarda embeddings faciales de forma segura (atomic write).
    """
    
    tmp = tempfile.mktemp()
    
    with open(tmp, "wb") as f:
        pickle.dump((names, encodings), f)
    shutil.move(tmp, data_path)
    logger.info("Base de datos facial guardada correctamente")



# =====================
# Cargar base de datos
# =====================

known_face_names, known_face_encodings = load_known_faces()


# ==========================================================
# ENDPOINT: RECONOCIMIENTO FACIAL
# ==========================================================

@app.route("/recognize", methods=["POST"])
def recognize():
        
    """
    @brief Reconoce rostros en una imagen enviada por cliente.
    """
    
    logger.info("Solicitud recibida en /recognize")

    data = request.get_json()
    
    if not data or "image" not in data:
        logger.error("Falta campo 'image' en la petición")
        return jsonify({"error": "Falta la imagen"}), 400

    # ------------------------------------------------------
    # Decodificación base64 → imagen
    # ------------------------------------------------------
    try:
        image_data = base64.b64decode(data["image"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        log("Error al decodificar la imagen recibida.", "\033[93m")
        return jsonify({"error": "Error al decodificar imagen"}), 400

    
    # ------------------------------------------------------
    # Detección facial
    # ------------------------------------------------------
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        logger.warning("No se detectaron rostros en la imagen")
        return jsonify({"recognized": [], "message": "No se detectó ningún rostro"})

    
    # ------------------------------------------------------
    # Comparación con base de datos
    # ------------------------------------------------------
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

    logger.info(f"Rostros reconocidos: {results}")

    return jsonify({
        "recognized": results,
        "message": f"Reconocidos: {', '.join(results)}"
    }) 


# ==========================================================
# ENDPOINT: REGISTRO DE USUARIO
# ==========================================================

@app.route("/register", methods=["POST"])
def register():
    """
    @brief Registra un nuevo usuario con múltiples imágenes.
    """
    
    # Registrar un nuevo usuario con varias imágenes.
    
    logger.info("Solicitud recibida en /register")

    data = request.get_json()

    if not data or "name" not in data or "images" not in data:
        logger.error("Faltan campos requeridos (name/images)")
        return jsonify({"error": "Faltan campos requeridos"}), 400

    name = data["name"].strip()
    images = data["images"]

    if not name:
        logger.warning("Nombre vacío recibido")
        return jsonify({"error": "El nombre no puede estar vacío"}), 400

    
    # ------------------------------------------------------
    # Carpeta del usuario
    # ------------------------------------------------------
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
            logger.warning(f"Imagen {i} corrupta")
            continue

        face_encs = face_recognition.face_encodings(rgb_frame)
        if face_encs:
            new_encodings.append(face_encs[0])
            cv2.imwrite(os.path.join(person_dir, f"{name}_{i+1}.jpg"), frame)

    
    # ------------------------------------------------------
    # Validación final
    # ------------------------------------------------------
    if not new_encodings:
        logger.error("Registro fallido: sin rostros válidos")
        return jsonify({"status": "error", "message": "No se detectaron rostros válidos"})

    
    # ------------------------------------------------------
    # Guardar en base de datos
    # ------------------------------------------------------
    known_face_names.extend([name] * len(new_encodings))
    known_face_encodings.extend(new_encodings)
    
    save_known_faces(known_face_names, known_face_encodings)

    logger.info(f"Usuario '{name}' registrado con éxito")

    return jsonify({
        "status": "ok",
        "message": f"{name} registrado con {len(new_encodings)} imágenes válidas"
    })



# ==========================================================
# INICIO DEL SERVIDOR
# ==========================================================
if __name__ == "__main__":
    log("Iniciando servidor Flask en http://0.0.0.0:5000", "\033[92m")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )