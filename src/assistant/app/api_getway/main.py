from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from assistant.app.api_getway.config import STATIC_DIR
from assistant.app.api_getway.api.routes_dashboard import router as dashboard_router
from assistant.app.api_getway.services.process_service import ProcessService


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Dashboard iniciado")

    yield

    print("Cerrando servicios...")

    ProcessService.stop_all()

    print("Servicios detenidos")


app = FastAPI(
    title="ROBOT ROJAZZ API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(dashboard_router)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")