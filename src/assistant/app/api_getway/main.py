# main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config import STATIC_DIR
from api.routes_face import router as face_router
from api.routes_llm import router as llm_router
from api.routes_dashboard import router as dashboard_router

##
# @file main.py
# @brief Punto de entrada principal y Pasarela de la API (API Gateway) del Robot.
# @details Inicializa la aplicación FastAPI, monta el enrutamiento de los microservicios
# (Face, LLM, Dashboard) y sirve los archivos web estáticos para la interfaz del usuario.
#

app = FastAPI(
    title="Robot API Gateway",
    version="1.0.0"
)

# ==========================================
# ROUTERS
# ==========================================

# Inyección de las rutas específicas del microservicio de Reconocimiento Facial
app.include_router(face_router)

# Inyección de las rutas específicas del servicio de Modelos de Lenguaje (LLM)
app.include_router(llm_router)

# Inyección de las rutas de control del panel de administración (Dashboard)
app.include_router(dashboard_router)

# ==========================================
# STATIC FILES
# ==========================================

# Montaje del directorio de archivos estáticos (HTML, CSS, JS, imágenes) en la ruta URL /static
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# ==========================================
# ROOT → DASHBOARD HTML
# ==========================================

@app.get("/")
def root():
    """
    @brief Endpoint raíz del servidor de la API.
    
    Se encarga de resolver y servir el archivo principal de la interfaz de usuario 
    HTML (Single Page Application) al acceder a la dirección base del Robot.
    
    @return FileResponse Instancia de respuesta con el contenido del fichero 'index.html'.
    """
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)