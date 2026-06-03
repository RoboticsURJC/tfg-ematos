           
import json
import logging
import os

from app.core.logs_to_server import RemoteHandler


# ==========================================================
# CONFIG
# ==========================================================

config_path = os.path.join(
    os.path.dirname(__file__),
    "../config/config.json"
)

with open(config_path, "r") as f:
    config = json.load(f)

# ~ SERVER_URL = config["server"]["log"]

SERVER_URL = "http://192.168.1.96:3000/client-log" 

# IMPORTANTE: debe ser URL COMPLETA del endpoint
# ejemplo: http://localhost:3000/client-log


# ==========================================================
# LOGGER
# ==========================================================

logger = logging.getLogger("robot")
logger.setLevel(logging.DEBUG)

# evita duplicados si se importa varias veces
if not logger.handlers:

    # --------------------------
    # consola local
    # --------------------------
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console)

    # --------------------------
    # remoto (dashboard)
    # --------------------------
    remote = RemoteHandler(SERVER_URL)
    remote.setLevel(logging.DEBUG)
    logger.addHandler(remote)


logger.propagate = False
            

