from fastapi import APIRouter

from services.log_service import (
    add_log,
    get_logs,
    clear_logs,
    get_all_logs
)

from services.process_service import ProcessService

router = APIRouter(tags=["Dashboard"])


# =====================================================
# START SERVICE (REAL)
# =====================================================

@router.post("/start/{service}")
def start_service(service: str):

    result = ProcessService.start(service)

    add_log(service, f"START REQUEST -> {result}")

    return result


# =====================================================
# STOP SERVICE (REAL)
# =====================================================

@router.post("/stop/{service}")
def stop_service(service: str):

    result = ProcessService.stop(service)

    add_log(service, f"STOP REQUEST -> {result}")

    return result


# =====================================================
# STATUS (OPCIONAL PERO RECOMENDADO)
# =====================================================

@router.get("/status")
def status():

    return ProcessService.status()


# =====================================================
# LOGS
# =====================================================

@router.get("/logs/{service}")
def logs(service: str):

    return {
        "logs": get_logs(service)
    }


# =====================================================
# CLEAR LOGS
# =====================================================

@router.delete("/logs/{service}")
def clear(service: str):

    clear_logs(service)

    return {"status": "ok"}


# =====================================================
# ALL LOGS
# =====================================================

@router.get("/logs")
def all_logs():

    return get_all_logs()