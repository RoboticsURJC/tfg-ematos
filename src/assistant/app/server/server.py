# server.py 
import os
import base64
from pathlib import Path
import pickle
import shutil
import tempfile
import cv2
import logging
import numpy as np
import face_recognition
from flask import Flask, request, jsonify
import sqlite3
import time
from datetime import datetime
import threading


# ==========================================================
# 🔧 CONFIGURACIÓN LOGGER
# ==========================================================

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


log_file = os.path.join(
    LOG_DIR,
    f"server_{datetime.now().strftime('%Y-%m-%d')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()  
    ]
)

logger = logging.getLogger("FaceServer")

app = Flask(__name__)


# ==========================================================
#  RUTAS DEL SISTEMA
# ==========================================================
# carpeta donde está server.py
curr_dir = Path(__file__).resolve().parent

# archivos/carpetas dentro de app/server
data_path = curr_dir / "known_faces.pkl"
people_path = curr_dir / "known_persons"

# robot_memory.db está en app/
db_path = curr_dir.parent / "robot_memory.db"

# crear carpetas
people_path.mkdir(parents=True, exist_ok=True)
db_path.parent.mkdir(parents=True, exist_ok=True)


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

def get_connection():
    """
    @brief Crea y devuelve una conexión a la base de datos SQLite.

    Esta función abre una conexión a la base de datos definida en DB_PATH
    y configura el acceso a las filas como diccionarios (sqlite3.Row),
    lo que permite acceder a las columnas por nombre en lugar de por índice.

    @return sqlite3.Connection Objeto de conexión a la base de datos.
    """
    
    conn = sqlite3.connect(
        db_path,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn

def init_database():
    """
    @brief Inicializa la base de datos SQLite y crea tablas.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            title TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            type TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

    logger.info("Base de datos SQLite inicializada")

# ==========================================
# Cargar base de datos
# ==========================================

known_face_names, known_face_encodings = load_known_faces()
init_database()

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
#  Memoria semantica del robot
# ==========================================================

@app.route("/remember", methods=["POST"])
def remember():

    data = request.get_json()

    user = data.get("user", "").strip()
    content = data.get("content", "").strip()

    if not user or not content:
        return jsonify({"error": "faltan campos"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO memories
        (user, content, created_at)
        VALUES (?, ?, ?)
    """, (
        user,
        content,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/memories/<user>", methods=["GET"])
def get_memories(user):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM memories
        WHERE user = ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (user,))

    rows = cursor.fetchall()

    conn.close()

    return jsonify([dict(r) for r in rows])

# ==========================================================
#  Recordatorios del usuario
# ==========================================================


@app.route("/add_reminder", methods=["POST"])
def add_reminder():
    
    data = request.get_json()
    
    user = data.get("user", "").strip()
    title = data.get("title")
    reminder_time = data.get("time")
    reminder_type = data.get("type")

    if not all([user, title, reminder_time, reminder_type]):
        return jsonify({"error": "faltan campos"}), 400
   
    
    try:
        datetime.fromisoformat(reminder_time)

    except ValueError:
        return jsonify({
            "error": "fecha inválida"
        }), 400
        
        
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
            INSERT INTO reminders
            (user, title, reminder_time, type, created_at)
            values (?, ?, ?, ?, ?)
        """, (
                user, 
                title, 
                reminder_time, 
                reminder_type,
                datetime.now().isoformat()
                )
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "ok"})

@app.route("/complete_reminder/<int:rid>", methods=["POST"])
def complete_reminder(rid):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reminders
        SET completed = 1
        WHERE id = ?
    """, (rid,))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/get_reminders/<user>", methods=["GET"])
def get_reminders(user):

    user = user.strip()

    if not user:
        return jsonify({"error": "user inválido"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM reminders
        WHERE user = ?
        ORDER BY reminder_time ASC
    """, (user,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

def reminder_scheduler():
    """
    Hilo en background que revisa recordatorios vencidos.
    """

    logger.info("Scheduler iniciado")

    while True:

        try:
            conn = get_connection()
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                SELECT *
                FROM reminders
                WHERE completed = 0
                AND reminder_time <= ?
            """, (now,))

            reminders = cursor.fetchall()

            for reminder in reminders:

                logger.info(
                    f"Reminder vencido: {reminder['title']}"
                )

                # ==================================================
                # AQUÍ VAN LAS ACCIONES AUTOMÁTICAS
                # ==================================================

                print(
                    f"[REMINDER] {reminder['user']}: "
                    f"{reminder['title']}"
                )

                # marcar completado automáticamente
                cursor.execute("""
                    UPDATE reminders
                    SET completed = 1
                    WHERE id = ?
                """, (reminder["id"],))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error scheduler: {e}")

        time.sleep(5)


# ==========================================================
# INICIO DEL SERVIDOR
# ==========================================================
if __name__ == "__main__":
    
    scheduler_thread = threading.Thread(
        target=reminder_scheduler,
        daemon=True
    )

    scheduler_thread.start()

    log("Iniciando servidor Flask en http://0.0.0.0:5000", "\033[92m")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )