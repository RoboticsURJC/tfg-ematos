import json
import logging
import os 
from app.core.logs_to_server import RemoteHandler


config_path = os.path.join(
    os.path.dirname(__file__),
    "../config/config.json"
)

print(config_path)

with open(config_path, "r") as f:
    config = json.load(f)

SERVER_URL = config["server"]["log"]


logger = logging.getLogger("robot")
logger.setLevel(logging.DEBUG)

remote = RemoteHandler(SERVER_URL)
remote.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

logger.addHandler(remote)