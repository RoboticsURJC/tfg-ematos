import subprocess
import os
import signal
from pathlib import Path
from services.log_service import add_log


class ProcessService:

    processes = {}

    # ==========================================================
    # ROOT REAL DEL PROYECTO
    # ==========================================================
    BASE_DIR = Path(__file__).resolve().parents[4]
    APP_DIR = BASE_DIR / "app"

    # ==========================================================
    # COMANDOS (FIXED)
    # ==========================================================
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
              "--host", "0.0.0.0",
              "--port", "5000"
          ]
      }

    # ==========================================================
    # WORKDIR (CLAVE DEL FIX)
    # ==========================================================
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

      process = cls.processes.get(service)

      if not process:
          return {"status": "OK", "message": "not running"}

      try:
          pgid = os.getpgid(process.pid)

          # intento suave
          os.killpg(pgid, signal.SIGTERM)

          # espera corta
          import time
          time.sleep(1)

          # kill duro si sigue vivo
          if process.poll() is None:
              os.killpg(pgid, signal.SIGKILL)

          del cls.processes[service]

          add_log(service, f"STOPPED PID={process.pid}")

          return {"status": "OK"}

      except Exception as e:
          add_log(service, f"STOP ERROR: {str(e)}")
          return {"status": "ERROR", "error": str(e)}

    # ---------------------------
    # CHECK RUNNING (TE FALTABA)
    # ---------------------------
    @classmethod
    def is_running(cls, service: str):

        process = cls.processes.get(service)

        if not process:
            return False

        return process.poll() is None