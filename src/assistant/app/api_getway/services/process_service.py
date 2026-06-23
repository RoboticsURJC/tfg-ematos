# services/process_service.py

import subprocess
import os
import signal
from pathlib import Path
import time
from services.log_service import add_log

##
# @file process_service.py
# @brief Servicio de gestión de subprocesos para los servidores asíncronos del sistema.
# @details Controla el ciclo de vida (inicio, parada y monitorización de estado) de los 
# microservicios de LLM y Reconocimiento Facial mediante comandos del sistema operativo.
#

class ProcessService:
    """
    @brief Clase encargada de administrar el arranque y detención controlada de procesos en segundo plano.
    """

    ## Contenedor en memoria (dict) para almacenar las instancias activas de tipo subprocess.Popen.
    processes = {}

    # ==========================================================
    # ROOT REAL DEL PROYECTO
    # ==========================================================
    ## Ruta absoluta calculada hacia el directorio raíz del proyecto (subiendo 4 niveles desde este archivo).
    BASE_DIR = Path(__file__).resolve().parents[4]
    
    ## Ruta absoluta hacia el subdirectorio 'app' del proyecto.
    APP_DIR = BASE_DIR / "app"

    # ==========================================================
    # COMANDOS (FIXED)
    # ==========================================================
    ## Diccionario con los comandos exactos y argumentos que utiliza uvicorn para levantar los servidores ASGI.
    COMMANDS = {
          "llm": [
              "python3",
              "-m",
              "uvicorn",
              "assistant.app.server.speaking_server:app",
              "--host", "0.0.0.0",
              "--port", "8000"
          ],

          "recognition": [
              "python3",
              "-m",
              "uvicorn",
              "assistant.app.server.server:app",
            #   "assistant.app.server.face_server:app",              
              "--host", "0.0.0.0",
              "--port", "5000"
          ]
      }

    # ==========================================================
    # WORKDIR (CLAVE DEL FIX)
    # ==========================================================
    ## Directorios de trabajo asignados a cada proceso para garantizar que Python resuelva las rutas de importación.
    WORKDIR = {
        "llm": str(BASE_DIR),
        "recognition": str(BASE_DIR)
    }
    
    print(WORKDIR)

    # ---------------------------
    # START
    # ---------------------------
    @classmethod
    def start(cls, service: str):
        """
        @brief Levanta un microservicio en segundo plano de manera asíncrona.
        
        Verifica si el servicio existe y si no está corriendo ya. Si pasa los filtros, inicializa 
        una nueva sesión de proceso (`start_new_session=True`) para encapsular las llamadas de terminal.
        
        @param service Identificador del servicio a iniciar ('llm' o 'recognition').
        
        @return dict Diccionario con el estado del comando operativo ('OK' con el PID o 'ERROR' con su traza).
        """
        if service not in cls.COMMANDS:
            return {"status": "ERROR", "error": "unknown service"}

        if cls.is_running(service):
            return {"status": "OK", "message": "already running"}

        try:
            process = subprocess.Popen(
                cls.COMMANDS[service],
                cwd=cls.WORKDIR[service],   
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True
            )

            cls.processes[service] = process
            add_log(service, f"STARTED PID={process.pid}")

            return {"status": "OK", "pid": process.pid}

        except Exception as e:
            add_log(service, f"START ERROR: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    # ---------------------------
    # STOP
    # ---------------------------
    @classmethod
    def stop(cls, service: str):
        """
        @brief Detiene de forma segura el microservicio indicado liberando sus recursos.
        
        Obtiene el ID de grupo de proceso (PGID) para enviar una señal de terminación suave (`SIGTERM`) 
        al árbol de procesos de Uvicorn. Si no responde tras un segundo de espera, se fuerza su cierre con `SIGKILL`.
        
        @param service Identificador del servicio a detener ('llm' o 'recognition').
        
        @return dict Diccionario con el estado del resultado de la cancelación.
        """
        process = cls.processes.get(service)

        if not process:
            return {"status": "OK", "message": "not running"}

        try:
            pgid = os.getpgid(process.pid)

            # Intento suave de detención a todo el árbol de procesos hijo
            os.killpg(pgid, signal.SIGTERM)

            # Espera corta de cortesía para el cierre controlado
            time.sleep(1)

            # Matar de forma forzosa (hard kill) si el proceso sigue respondiendo en el bucle
            if process.poll() is None:
                os.killpg(pgid, signal.SIGKILL)

            del cls.processes[service]
            add_log(service, f"STOPPED PID={process.pid}")

            return {"status": "OK"}

        except Exception as e:
            add_log(service, f"STOP ERROR: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    # ---------------------------
    # CHECK RUNNING
    # ---------------------------
    @classmethod
    def is_running(cls, service: str):
        """
        @brief Evalúa si el subproceso asociado a un servicio sigue activo.
        
        Utiliza el método `.poll()` nativo de Python; si retorna `None`, significa que el proceso 
        sigue en ejecución y no ha terminado.
        
        @param service Identificador del servicio a monitorizar.
        
        @return bool Verdadero (`True`) si está corriendo, Falso (`False`) en caso contrario.
        """
        process = cls.processes.get(service)

        if not process:
            return False

        return process.poll() is None