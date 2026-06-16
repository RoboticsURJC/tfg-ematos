# config.py

import os
import json

##
# @file config_manager.py
# @brief Gestor centralizado de configuraciones basado en archivos JSON.
# @details Carga de manera perezosa (Lazy loading) y unificada los parámetros lógicos, 
# rutas y direcciones URL de los microservicios del sistema desde un fichero JSON en disco.
#

class Config:
    """
    @brief Clase Singleton encargada de leer, almacenar y proveer acceso a los ajustes del sistema.
    @details Asegura que el archivo de configuración en disco se lea una única vez durante todo 
    El ciclo de vida de la aplicación, manteniendo los datos accesibles en memoria de forma segura.
    """

    ## Instancia única global de la clase (patrón Singleton).
    _instance = None

    ## Diccionario en memoria que contiene la estructura completa de datos JSON leída.
    _data = None

    def __new__(cls):
        """
        @brief Constructor de bajo nivel de Python modificado para implementar el patrón Singleton.
        @details Intercepta la creación de la clase; si la instancia `_instance` no existe, 
        Crea el objeto en memoria e invoca automáticamente al método de carga interna `_load()`.
        
        @return Config La instancia única y centralizada del gestor de configuración.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        """
        @brief Resuelve las rutas del sistema de archivos de forma dinámica y parsea el archivo JSON.
        @details Sube desde el directorio actual (`app/core/`) un nivel para posicionarse en la raíz 
        Del proyecto, localiza la ruta `./config/config.json` y vuelca su contenido en el diccionario.
        
        @exception FileNotFoundError Lanzada si el archivo físico JSON no se encuentra en la ruta esperada.
        """
        # Calcular de forma absoluta el directorio raíz del proyecto subiendo un nivel desde la ubicación de este script
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        config_path = os.path.join(base_dir, "config", "config.json")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config no encontrado: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    # =========================
    # ACCESSORS
    # =========================

    def get(self, key, default=None):
        """
        @brief Accesor genérico para recuperar cualquier clave de primer nivel del archivo de configuración.
        
        @param key Cadena de texto con el nombre del parámetro o sección que se desea consultar.
        @param default Valor de salvaguarda (fallback) a retornar en caso de que la clave no exista.
        
        @return mixed El valor asociado a la clave (dict, list, str, int, etc.) o el valor por defecto.
        """
        return self._data.get(key, default)

    def server(self):
        """
        @brief Recupera el bloque o sección dedicada a la configuración de los servidores de red.
        
        @return dict Diccionario interno con las directivas de red o un diccionario vacío si no está definido.
        """
        return self._data.get("server", {})

    def recognition_url(self):
        """
        @brief Extrae la URL de red configurada específicamente para el microservicio de reconocimiento facial.
        
        @return str Dirección URL absoluta del servidor de visión o None si no se encuentra especificada.
        """
        return self.server().get("recognition_url")

    def llm_url(self):
        """
        @brief Extrae la URL de red configurada específicamente para el microservicio del modelo de lenguaje (LLM).
        
        @return str Dirección URL absoluta del servidor de Inteligencia Artificial o None si no se encuentra especificada.
        """
        return self.server().get("llm_url")