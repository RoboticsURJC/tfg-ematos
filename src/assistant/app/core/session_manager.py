# app/core/session_manager.py

import json
import os
import time

##
# @file session_manager.py
# @brief Componente de persistencia y gestión de estados de sesión del usuario.
# @details Se encarga de monitorizar de forma volátil y persistente el usuario activo del robot,
# controlando las marcas de tiempo de inicio de sesión y escribiendo su estado en ficheros de configuración JSON.
#

class SessionManager:
    """
    @brief Gestor del ciclo de vida de la sesión activa del robot.
    @details Centraliza los mecanismos de autenticación local, cierre de sesión y la
    recuperación automática de estados ante reinicios imprevistos del software (failover).
    """

    def __init__(self, data_path=None):
        """
        @brief Inicializa el administrador resolviendo la ruta del almacén de datos.
        @details Si no se provee una ruta específica para el archivo de sesión, este calcula por defecto
        la ubicación en la carpeta de datos del proyecto (`../data/session.json`) e intenta restaurar 
        el último estado llamando internamente a `load()`.
        
        @param data_path Ruta absoluta opcional hacia el archivo físico JSON de persistencia.
        """
        base = os.path.dirname(
            os.path.abspath(__file__)
        )

        if data_path is None:
            data_path = os.path.join(
                base,
                "..",
                "data",
                "session.json"
            )

        ## Ruta del archivo en el disco donde se vuelcan los estados de autenticación.
        self.data_path = data_path

        ## Identificador o nombre de pila del perfil de usuario actualmente autenticado (None si no hay ninguno).
        self.current_user = None

        ## Marca de tiempo Unix (epoch) que registra el momento exacto en el que el usuario inició sesión.
        self.login_time = None

        # Intento de restauración automática del estado previo al instanciar el manager
        self.load()

    # =========================================================
    # LOGIN
    # =========================================================

    def login(self, username):
        """
        @brief Establece el perfil del usuario activo en el sistema y congela su marca de tiempo.
        @details Actualiza las propiedades internas en memoria y llama inmediatamente al método de escritura
        física `save()` para sincronizar el estado.
        
        @param username Nombre de pila o identificador del usuario que ha iniciado sesión.
        """
        self.current_user = username
        self.login_time = time.time()
        self.save()

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(self):
        """
        @brief Invalida y limpia por completo las variables del usuario activo en el sistema.
        @details Setea las propiedades a `None` y purga el archivo JSON persistente invocando a `save()`.
        """
        self.current_user = None
        self.login_time = None
        self.save()

    # =========================================================
    # STATE
    # =========================================================

    @property
    def is_logged(self):
        """
        @brief Propiedad calculada (Getter) que dictamina si existe una sesión de usuario abierta.
        
        @return bool True si un usuario válido tiene el control del dispositivo, False en caso contrario.
        """
        return self.current_user is not None

    # =========================================================
    # SAVE
    # =========================================================

    def save(self):
        """
        @brief Serializa el estado actual de la sesión en disco en formato JSON.
        @details Asegura de forma tolerante a fallos la existencia de la estructura de directorios 
        destino mediante `os.makedirs` antes de proceder con el volcado físico de datos.
        """
        try:
            os.makedirs(
                os.path.dirname(self.data_path),
                exist_ok=True
            )

            data = {
                "current_user": self.current_user,
                "login_time": self.login_time
            }

            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            # Captura de salvaguarda ante fallos de permisos de escritura o espacio en la tarjeta SD
            print("SESSION SAVE ERROR:", e)

    # =========================================================
    # LOAD
    # =========================================================

    def load(self):
        """
        @brief Lee y deserializa el archivo de sesión en disco para restaurar el estado del sistema.
        @details Si el archivo no existe en la ruta configurada, el método aborta silenciosamente la ejecución 
        sin alterar las propiedades por defecto.
        """
        if not os.path.exists(self.data_path):
            return

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.current_user = data.get("current_user")
            self.login_time = data.get("login_time")

        except Exception as e:
            # Captura de salvaguarda ante corrupciones de estructura del fichero JSON
            print("SESSION LOAD ERROR:", e)