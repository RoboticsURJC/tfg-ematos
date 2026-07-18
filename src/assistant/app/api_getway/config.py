from pathlib import Path

# ==========================================
# BASE DIR
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

# ==========================================
# STATIC / LOGS
# ==========================================

STATIC_DIR = BASE_DIR / "static"
LOG_DIR = BASE_DIR / "logs"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# MICROSERVICIOS
# ==========================================

FACE_SERVER_URL = "http://localhost:5000"
LLM_SERVER_URL = "http://localhost:8000"
LOG_SERVER_URL = "http://localhost:6000"

# ==========================================
# DASHBOARD
# ==========================================

HOST = "0.0.0.0"
PORT = 3000