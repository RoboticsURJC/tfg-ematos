# services/face_service.py

import requests
from services.log_service import add_log

##
# @file face_service.py
# @brief Servicio cliente para la comunicación con el microservicio de Reconocimiento Facial.
# @details Gestiona las peticiones HTTP (POST y GET) hacia el backend de IA local encargado del procesamiento de rostros y bases de datos semánticas.
#

FACE_URL = "http://localhost:5000"


class FaceService:
    """
    @brief Clase estática que encapsula los servicios de reconocimiento, registro y memoria facial.
    """

    @staticmethod
    def recognize(image: str):
        """
        @brief Envía una imagen para identificar el rostro presente en ella.
        
        Realiza una petición POST al endpoint de reconocimiento y registra el evento en el historial de logs.
        
        @param image Imagen codificada (normalmente en Base64 o ruta) que contiene el rostro a reconocer.
        
        @return dict Diccionario con la respuesta del microservicio (datos del usuario identificado o estado de error).
        """
        try:
            r = requests.post(
                f"{FACE_URL}/recognize",
                json={"image": image},
                timeout=30
            )

            data = r.json()
            add_log("recognition", "Face recognition executed")
            return data

        except Exception as e:
            add_log("recognition", f"ERROR recognize: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def register(name: str, images: list):
        """
        @brief Registra un nuevo usuario asociándolo a un conjunto de imágenes de entrenamiento.
        
        Envía los datos mediante una petición POST al microservicio para extraer los patrones faciales característicos.
        
        @param name Nombre o identificador único del nuevo usuario.
        @param images Lista de imágenes (en formato Base64 o rutas) que muestran el rostro desde diferentes ángulos.
        
        @return dict Respuesta del servidor que confirma el éxito del registro o detalla el fallo.
        """
        try:
            r = requests.post(
                f"{FACE_URL}/register",
                json={
                    "name": name,
                    "images": images
                },
                timeout=60
            )

            data = r.json()
            add_log("recognition", f"User registered: {name}")
            return data

        except Exception as e:
            add_log("recognition", f"ERROR register: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def memories(user: str):
        """
        @brief Recupera la base de conocimientos o memorias vinculadas a un usuario específico.
        
        Realiza una consulta GET para extraer toda la información contextual almacenada sobre la persona indicada.
        
        @param user Nombre o identificador único del usuario consultado.
        
        @return dict/list Datos históricos y notas guardadas del usuario, o un diccionario con estado de error.
        """
        try:
            r = requests.get(
                f"{FACE_URL}/memories/{user}",
                timeout=10
            )
            return r.json()

        except Exception as e:
            add_log("recognition", f"ERROR memories: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def remember(user: str, content: str):
        """
        @brief Almacena un nuevo dato o recuerdo textual en el perfil del usuario.
        
        Envía información semántica mediante una petición POST para enriquecer el contexto que el sistema posee sobre esa persona.
        
        @param user Nombre o identificador único del usuario al que se le asocia el recuerdo.
        @param content Texto descriptivo con la información que el sistema debe memorizar.
        
        @return dict Resultado de la operación devuelto por el backend de almacenamiento.
        """
        try:
            r = requests.post(
                f"{FACE_URL}/remember",
                json={
                    "user": user,
                    "content": content
                },
                timeout=10
            )
            return r.json()

        except Exception as e:
            add_log("recognition", f"ERROR remember: {str(e)}")
            return {"status": "ERROR", "error": str(e)}