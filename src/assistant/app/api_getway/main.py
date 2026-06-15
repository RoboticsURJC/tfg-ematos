from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import STATIC_DIR

from api.routes_face import router as face_router
from api.routes_llm import router as llm_router
from api.routes_dashboard import router as dashboard_router


app = FastAPI(
    title="Robot API Gateway",
    version="1.0.0"
)

# ==========================================
# ROUTERS
# ==========================================

app.include_router(face_router)
app.include_router(llm_router)
app.include_router(dashboard_router)

# ==========================================
# STATIC FILES
# ==========================================

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

    index_file = STATIC_DIR / "index.html"

    return FileResponse(index_file)