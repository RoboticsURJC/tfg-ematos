import subprocess
import os
import signal
import threading
import time

from pathlib import Path

from assistant.app.api_getway.services.log_service import add_log


class ProcessService:

    processes = {}

    BASE_DIR = Path(__file__).resolve().parents[4]

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

    WORKDIR = {
        "llm": str(BASE_DIR),
        "recognition": str(BASE_DIR)
    }

    @classmethod
    def start(cls, service: str):

        if service not in cls.COMMANDS:
            return {"status": "ERROR", "error": "Unknown service"}

        if cls.is_running(service):
            return {"status": "OK", "message": "Already running"}

        try:

            process = subprocess.Popen(
                cls.COMMANDS[service],
                cwd=cls.WORKDIR[service],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True
            )

            cls.processes[service] = process

            add_log(service, f"STARTED PID={process.pid}")

            threading.Thread(
                target=cls._pipe_logs,
                args=(service, process),
                daemon=True
            ).start()

            return {
                "status": "OK",
                "pid": process.pid
            }

        except Exception as e:

            add_log(service, f"START ERROR: {e}")

            return {
                "status": "ERROR",
                "error": str(e)
            }

    @classmethod
    def stop(cls, service: str):

        process = cls.processes.get(service)

        if process is None:
            return {"status": "OK", "message": "Not running"}

        try:

            if process.poll() is None:

                pgid = os.getpgid(process.pid)

                os.killpg(pgid, signal.SIGTERM)

                time.sleep(1)

                if process.poll() is None:
                    os.killpg(pgid, signal.SIGKILL)

                process.wait(timeout=2)

            cls.processes.pop(service, None)

            add_log(service, f"STOPPED PID={process.pid}")

            return {"status": "OK"}

        except Exception as e:

            add_log(service, f"STOP ERROR: {e}")

            return {
                "status": "ERROR",
                "error": str(e)
            }

    @classmethod
    def stop_all(cls):

        add_log("SYSTEM", "Stopping all services")

        for service in list(cls.processes.keys()):
            cls.stop(service)

    @classmethod
    def is_running(cls, service: str):

        process = cls.processes.get(service)

        return process is not None and process.poll() is None

    @classmethod
    def status(cls):

        return {
            name: cls.is_running(name)
            for name in cls.COMMANDS.keys()
        }

    @classmethod
    def _pipe_logs(cls, service: str, process: subprocess.Popen):

        def reader(pipe):

            for line in iter(pipe.readline, ""):

                if line:
                    add_log(service, line.strip())

        if process.stdout:
            threading.Thread(
                target=reader,
                args=(process.stdout,),
                daemon=True
            ).start()

        if process.stderr:
            threading.Thread(
                target=reader,
                args=(process.stderr,),
                daemon=True
            ).start()