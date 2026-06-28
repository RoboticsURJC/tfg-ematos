# server.py 

"""
@file server.py
@brief Servidor central del robot: reconocimiento facial, memoria semántica y alarmas.
@details Levanta un servicio web API REST basado en Flask que gestiona:
- Procesamiento y decodificación de tramas base64 para el motor face_recognition.
- Base de datos facial persistente mediante serialización atómica (Pickle + Tempfile).
- Almacenamiento e historial de memorias semánticas y alertas en SQLite.
- Hilo planificador en segundo plano (daemon thread) para la auditoría de recordatorios vencidos.
"""

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
#  CONFIGURACIÓN LOGGER
# ==========================================================

## Directorio absoluto asignado para el almacenamiento físico de logs de auditoría.
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

## Nombre del fichero de log rotativo diario computado de forma dinámica.
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

## Instancia del registrador (logger) asignado para el backend de reconocimiento.
logger = logging.getLogger("FaceServer")

## Instancia global de la aplicación web WSGI de Flask.
app = Flask(__name__)


# ==========================================================
#  RUTAS DEL SISTEMA
# ==========================================================

## Ruta absoluta del directorio raíz donde se localiza el script del servidor.
curr_dir = Path(__file__).resolve().parent

## Ruta del almacén binario pkl que guarda la base de datos de embeddings vectoriales.
data_path = curr_dir / "known_faces.pkl"

## Ruta hacia la galería física de imágenes de personas registradas en el sistema.
people_path = curr_dir / "known_persons"

## Ubicación del archivo de base de datos relacional SQLite que aloja la persistencia relacional.
db_path = curr_dir.parent / "robot_memory.db"

# Creación e inicialización forzada de los directorios clave del servidor en el sistema de archivos
people_path.mkdir(parents=True, exist_ok=True)
db_path.parent.mkdir(parents=True, exist_ok=True)


def log(msg, color="\033[96m"):
    """
    @brief Imprime mensajes formateados por la salida estándar utilizando códigos de color ANSI.
    
    @param msg Cadena de texto o cuerpo del mensaje informativo.
    @param color Código ANSI de color para la terminal (por defecto cian '\033[96m').
    """
    now = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{now}] {msg}\033[0m")
    


# ==========================================================
# CARGA / GUARDADO DE BASE DE DATOS
# ==========================================================

def load_known_faces():
    """
    @brief Carga los embeddings faciales y nombres de referencia desde el disco duro.
    @details Intenta deserializar el archivo `.pkl`. Si no se localiza en la ruta del sistema, 
    inicializa estructuras vacías mitigando interrupciones en el arranque del servidor.
    
    @return tuple Una tupla estructurada en formato `(names, encodings)` donde:
           - `names` (list): Nombres de pila de los usuarios.
           - `encodings` (list): Vectores de características faciales multidimensionales (128-d).
    """
    if os.path.exists(data_path):
        with open(data_path, "rb") as f:
            logger.info("Base de datos facial cargada correctamente")
            return pickle.load(f)
        
    logger.warning("No existe base de datos previa. Inicializando vacía.")
    return [], []


def save_known_faces(names, encodings):
    """
    @brief Guarda los embeddings vectoriales de rostros mediante una operación de escritura atómica.
    @details Escribe el payload binario en un archivo temporal intermedio para posteriormente realizar 
    un desplazamiento atómico (`shutil.move`), blindando la base de datos ante corrupciones críticas de 
    datos si el proceso sufre un corte eléctrico imprevisto a mitad de escritura.
    
    @param names Lista consolidada con los nombres de los usuarios indexados.
    @param encodings Lista de vectores de características (`numpy.ndarray`) de los rostros detectados.
    """
    tmp = tempfile.mktemp()
    
    with open(tmp, "wb") as f:
        pickle.dump((names, encodings), f)
    shutil.move(tmp, data_path)
    logger.info("Base de datos facial guardada correctamente")


def get_connection():
    """
    @brief Crea y parametriza una nueva conexión atómica hacia la base de datos SQLite.
    @details Modifica la propiedad `row_factory` al valor nativo `sqlite3.Row` para posibilitar el 
    mapeo por diccionario (clave-valor). Desactiva el flag de aserción de hilos (`check_same_thread=False`) 
    permitiendo consultas seguras desde peticiones HTTP concurrentes y el daemon de alertas.

    @return sqlite3.Connection Objeto activo de conexión a la base de datos SQLite.
    """
    conn = sqlite3.connect(
        db_path,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    @brief Inicializa la estructura del esquema relacional y crea las tablas si no existen.
    @details Levanta de forma automática las tablas de entidad `reminders` (alertas de medicación 
    y tareas) y `memories` (registro conversacional de la memoria semántica a largo plazo del robot).
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

# ==========================================================
# Ejecución de rutinas de carga en el inicio del script
# ==========================================================
## Vector global en memoria con los nombres ordenados de las caras conocidas.
known_face_names, ## Vector global en memoria con los embeddings multidimensionales de referencia.
known_face_encodings = load_known_faces()
init_database()


# ==========================================================
# ENDPOINT: RECONOCIMIENTO FACIAL
# ==========================================================

@app.route("/recognize", methods=["POST"])
def recognize():
    """
    @brief Endpoint HTTP POST: Procesa e identifica caras a partir de un fotograma de cámara.
    @details Decodifica una trama binaria desde base64, reconstruye el arreglo matricial de color 
    mediante OpenCV, calcula los vectores de 128 dimensiones con el algoritmo HOG (Histogram of Oriented Gradients) 
    y deduce las distancias euclidianas relativas (`face_distance`) para discernir la identidad más precisa.
    
    @return Response Objeto JSON con el array de nombres identificados (`recognized`) y códigos HTTP estándar.
    """
    logger.info("Solicitud recibida en /recognize")
    data = request.get_json()
    
    if not data or "image" not in data:
        logger.error("Falta campo 'image' en la petición")
        return jsonify({"error": "Falta la imagen"}), 400

    # Decodificación base64 → Array binario → Imagen Matricial OpenCV (BGR)
    try:
        image_data = base64.b64decode(data["image"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        log("Error al decodificar la imagen recibida.", "\033[93m")
        return jsonify({"error": "Error al decodificar imagen"}), 400

    # Conversión obligatoria de espacio de color BGR a RGB exigida por dlib/face_recognition
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        logger.warning("No se detectaron rostros en la imagen")
        return jsonify({"recognized": [], "message": "No se detectó ningún rostro"})

    results = []
    for encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, encoding)
        name = "Desconocido"
        face_distances = face_recognition.face_distance(known_face_encodings, encoding)

        if len(face_distances) > 0:
            # Determinación de la menor distancia euclidiana (el rostro más idéntico matemáticamente)
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
    @brief Endpoint HTTP POST: Registra un nuevo usuario asociándolo a un set de imágenes facíales.
    @details Crea de forma dinámica la estructura física del perfil en disco, barre la colección de 
    imágenes extrayendo sus características faciales válidas, escribe el fotograma JPG en la galería y 
    actualiza los arrays en memoria sincronizando los datos con la base de datos atómica mediante `save_known_faces`.
    
    @return Response Objeto de respuesta JSON reflejando el estatus de la operación (`ok`/`error`).
    """
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

    # Generación y reserva del directorio específico del perfil del usuario
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
            # Salvaguarda del archivo fotográfico físico de auditoría en disco
            cv2.imwrite(os.path.join(person_dir, f"{name}_{i+1}.jpg"), frame)

    if not new_encodings:
        logger.error("Registro fallido: sin rostros válidos detectados")
        return jsonify({"status": "error", "message": "No se detectaron rostros válidos"})

    # Extensión de la estructura de datos activa en memoria RAM
    known_face_names.extend([name] * len(new_encodings))
    known_face_encodings.extend(new_encodings)
    
    # Commit físico persistente en disco
    save_known_faces(known_face_names, known_face_encodings)
    logger.info(f"Usuario '{name}' registrado con éxito")

    return jsonify({
        "status": "ok",
        "message": f"{name} registrado con {len(new_encodings)} imágenes válidas"
    })


# ==========================================================
#  Memoria semántica del robot
# ==========================================================

@app.route("/remember", methods=["POST"])
def remember():
    """
    @brief Endpoint HTTP POST: Inyecta una nueva traza de conocimiento en la memoria relacional del robot.
    
    @return Response Estado de confirmación JSON.
    """
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
    """
    @brief Endpoint HTTP GET: Extrae los últimos 20 hechos o recuerdos guardados asociados a un perfil.
    
    @param user Nombre de pila identificativo del usuario a consultar.
    @return Response Array JSON con la estructura completa de los registros coincidentes.
    """
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
    """
    @brief Endpoint HTTP POST: Da de alta un recordatorio validando rigurosamente la estampa temporal.
    @details Fuerza la validación del campo de tiempo mediante `fromisoformat()` para garantizar que la 
    sintaxis del reloj coincide con la norma internacional, previniendo excepciones en el daemon.
    
    @return Response Estado de confirmación JSON con código de error HTTP en caso de fecha desalineada.
    """
    data = request.get_json()
    
    user = data.get("user", "").strip()
    title = data.get("title")
    reminder_time = data.get("time")
    reminder_type = data.get("type")

    if not all([user, title, reminder_time, reminder_type]):
        return jsonify({"error": "faltan campos"}), 400
   
    try:
        # Validación sintáctica preventiva contra inyecciones de fecha corruptas
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
    """
    @brief Endpoint HTTP POST: Conmuta de forma explícita el bit de completado de una alerta.
    
    @param rid Clave primaria identificadora (`id`) del recordatorio en la tabla SQLite.
    @return Response Estado de confirmación JSON.
    """
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
    """
    @brief Endpoint HTTP GET: Lista cronológicamente todos los recordatorios activos e históricos de un usuario.
    
    @param user Nombre del perfil del usuario bajo consulta.
    @return Response Lista de objetos JSON mapeados.
    """
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
    @brief Proceso planificador e hilo demonio (Background Scheduler).
    @details Se ejecuta de forma infinita en segundo plano cada 5 segundos barriendo la tabla 
    de la base de datos. Si localiza un registro no completado cuya fecha planificada sea igual 
    o menor al tiempo ISO actual, dispara un evento de alarma y conmuta de forma automática 
    su estado a completado (`completed = 1`).
    """
    logger.info("Scheduler iniciado")

    while True:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            # Búsqueda selectiva de alarmas activas vencidas en el tiempo
            cursor.execute("""
                SELECT *
                FROM reminders
                WHERE completed = 0
                AND reminder_time <= ?
            """, (now,))

            reminders = cursor.fetchall()

            for reminder in reminders:
                logger.info(f"Reminder vencido detectado: {reminder['title']}")

                # ==================================================
                # ZONA DE EXTENSIÓN: ACCIONES AUTOMÁTICAS HARDWARE
                # ==================================================
                print(
                    f"[REMINDER EXEC] {reminder['user']}: "
                    f"{reminder['title']}"
                )

                # Cierre de ciclo automático de la alerta para impedir re-disparos cíclicos
                cursor.execute("""
                    UPDATE reminders
                    SET completed = 1
                    WHERE id = ?
                """, (reminder["id"],))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error crítico en bucle interno del scheduler: {e}")

        # Latencia periódica fija para no saturar el bus E/S del microcontrolador o CPU
        time.sleep(5)


# ==========================================================
# INICIO DEL SERVIDOR
# ==========================================================
if __name__ == "__main__":
    
    # Instanciación y disparo del hilo de control asíncrono para las alarmas de medicación
    scheduler_thread = threading.Thread(
        target=reminder_scheduler,
        daemon=True  # Se configura como Daemon para que muera de forma limpia al tumbar el hilo principal
    )
    scheduler_thread.start()

    log("Iniciando servidor Flask en http://0.0.0.0:5000", "\033[92m")

    # Inicialización del entorno de Flask. Se fuerza debug=False para evitar colisiones con el Threading nativo
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
