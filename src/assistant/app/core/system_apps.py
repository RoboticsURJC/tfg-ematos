# system_apps.py

import subprocess
import shutil
import time
from app.core.logger import logger

##
# @file system_apps.py
# @brief Lanzador y enrutador de aplicaciones del sistema (tanto internas como externas).
# @details Clasifica las peticiones del Launcher, desviando las aplicaciones internas de PyQt 
# hacia el controlador de ventanas y ejecutando las herramientas externas del S.O. Linux como subprocesos independientes.
#

class SystemApps:
    """
    @brief Clase estática encargada del enrutamiento y ejecución segura de aplicaciones.
    @details Incorpora un mecanismo electrónico/lógico anti-rebote (de-bounce) para pantallas táctiles.
    """

    ## Diccionario de mapeo que define el identificador de la aplicación y su comando o ruta interna de ejecución.
    APPS = {
        "notes": "internal:notes",
        "browser": "internal:browser",
        "calendar": "internal:calendar",
        "calculator": ["galculator", "gnome-calculator", "calc"],
        "reminder": "internal:reminder",
        "games": "internal:games",
        "settings": "internal:settings"
    }

    # =========================================================
    # SEGURO ANTI-REBOTE TRÁFICO TÁCTIL
    # =========================================================
    
    ## Marca de tiempo Unix (en segundos) que registra el momento exacto de la última ejecución exitosa.
    _last_launch_time = 0
    
    ## Intervalo de tiempo mínimo (en segundos) requerido entre pulsaciones consecutivas para mitigar clics fantasmas.
    _cooldown_seconds = 2.0  

    @classmethod
    def launch(cls, app_id):
        """
        @brief Ejecuta o enruta una aplicación del sistema aplicando filtros de seguridad táctil.
        @details Evalúa la diferencia de tiempo desde la última pulsación para interceptar dobles clics 
        accidentales. Si el ID de la aplicación está marcado como `internal:`, delega el control retornando 
        el prefijo; si es una lista de comandos del sistema, barre el PATH del sistema operativo usando 
        `shutil.which` para lanzar el binario disponible en segundo plano de forma no bloqueante.
        
        @param app_id Identificador textual único de la aplicación que se desea inicializar.
        
        @return mixed Retorna una cadena str con el prefijo 'internal:' si la app pertenece a la UI nativa.
        @return bool Retorna True si la aplicación externa se ejecutó con éxito, o False ante errores o app no registrada.
        """
        # 1. Verificar si el usuario ha pulsado demasiado rápido (Doble click accidental o rebote físico)
        current_time = time.time()
        if (current_time - cls._last_launch_time) < cls._cooldown_seconds:
            logger.warning(f"[SYSTEM APPS] Bloqueado click fantasma/doble en: '{app_id}'")
            
            # Devolvemos el comportamiento de acción programado para que la interfaz no se congele, pero mitigamos el re-lanzamiento
            action = cls.APPS.get(app_id)
            if isinstance(action, str) and action.startswith("internal:"):
                return action
            return True

        action = cls.APPS.get(app_id)

        if not action:
            logger.error(f"[SYSTEM APPS] Aplicación no registrada: {app_id}")
            return False

        # =========================================================
        # APPS INTERNAS (UI PYQT)
        # =========================================================
        if isinstance(action, str) and action.startswith("internal:"):
            cls._last_launch_time = current_time  # Actualizamos el temporizador de seguridad
            return action   # IMPORTANTE: No ejecutamos subprocess, el controlador principal se encarga del stack

        # =========================================================
        # APPS DEL SISTEMA (PROCESOS EXTERNOS)
        # =========================================================
        if isinstance(action, list):
            for app in action:
                # Comprobar si el binario de la aplicación existe y es ejecutable en el entorno actual
                if shutil.which(app):
                    try:
                        # Registramos el tiempo justo antes de realizar la bifurcación del subproceso
                        cls._last_launch_time = current_time
                        
                        # Ejecución asíncrona mediante un subproceso independiente para evitar congelar el hilo de la UI
                        subprocess.Popen([app])
                        logger.info(f"[SYSTEM APP] Aplicación lanzada: {app}")
                        return True

                    except Exception as e:
                        logger.error(f"[SYSTEM APP] Error lanzando {app}: {e}")

            logger.error(f"[SYSTEM APP] No se encontró ninguna app válida instalada para {app_id}")
            return False

        return False
