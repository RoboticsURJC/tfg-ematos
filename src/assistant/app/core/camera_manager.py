# app/core/camera_manager.py

import cv2
from app.core.logger import logger

##
# @file camera_manager.py
# @brief Administrador y controlador de hardware para la cámara del robot.
# @details Implementa un patrón de diseño Singleton para asegurar el acceso centralizado y 
# compartido al flujo de video de OpenCV (cv2.VideoCapture) desde múltiples hilos o componentes.
#

class CameraManager:
    """
    @brief Clase encargada de la inicialización, captura de fotogramas y liberación de la cámara.
    @details Evita colisiones de hardware al centralizar el descriptor de archivo de vídeo del sistema.
    """

    ## Instancia única de la clase para el patrón Singleton.
    _instance = None

    def __init__(self):
        """
        @brief Constructor privado/interno de la clase.
        """
        ## Objeto de captura de vídeo de OpenCV (cv2.VideoCapture) o None si está cerrada.
        self.cap = None

    # =========================================
    # SINGLETON
    # =========================================
    @classmethod
    def get(cls):
        """
        @brief Recupera la instancia única global del administrador de la cámara.
        @details Si no se ha instanciado previamente, la crea e inicializa el objeto en memoria.
        
        @return CameraManager Instancia única de control de la cámara.
        """
        if cls._instance is None:
            cls._instance = CameraManager()
        return cls._instance

    # =========================================
    # OPEN CAMERA
    # =========================================
    def open(self):
        """
        @brief Abre e inicializa el dispositivo físico de captura de video.
        @details Configura la API del driver nativo para Linux (CAP_V4L2), establece una resolución 
        estándar estricta de 640x480 para economizar procesamiento de CPU en la Raspberry Pi y limita 
        el tamaño del buffer de fotogramas a 1 para garantizar que el último frame leído sea siempre el actual.
        
        @exception RuntimeError Lanzada si el sistema operativo no puede reclamar el acceso al índice del hardware.
        
        @return cv2.VideoCapture Descriptor de captura activo de OpenCV.
        """
        # Evitar re-inicializaciones si el canal ya se encuentra abierto y respondiendo
        if self.cap is not None and self.cap.isOpened():
            return self.cap

        logger.info("[CAMERA MANAGER] Abriendo cámara compartida")

        # Inicialización forzando el backend Video4Linux2 (V4L2) idóneo para entornos Raspberry Pi
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            logger.info("[CAMERA MANAGER] No se ha podido abrir la cámara")
            raise RuntimeError("No se pudo abrir la cámara")

        # Configuración de propiedades físicas del hardware de captura
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Buffer de tamaño 1 para eliminar el desfase de colas y leer siempre imágenes en tiempo real
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        return self.cap

    # =========================================
    # READ
    # =========================================
    def read(self):
        """
        @brief Captura y extrae el siguiente frame de video de la cámara activa.
        @details Si la cámara se encuentra cerrada al invocar este método, realiza un intento 
        automático de apertura controlada llamando internamente a `open()`.
        
        @return tuple Una tupla compuesta por `(retval, image)` donde `retval` es un booleano de éxito 
        e `image` es una matriz NumPy (BGR) que contiene el fotograma capturado.
        """
        if self.cap is None:
            self.open()

        return self.cap.read()

    # =========================================
    # RELEASE
    # =========================================
    def release(self):
        """
        @brief Libera los recursos de hardware asociados al dispositivo de captura.
        @details Cierra el descriptor de archivo nativo de la cámara para permitir que otras 
        aplicaciones del sistema operativo puedan reutilizar el puerto de vídeo.
        """
        if self.cap is not None:
            logger.info("[CAMERA MANAGER] Liberando cámara")
            self.cap.release()
            self.cap = None