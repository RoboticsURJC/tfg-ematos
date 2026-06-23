# app/routes/dashboard.py

from fastapi import APIRouter
from services.log_service import (
    add_log,
    get_logs,
    clear_logs,
    get_all_logs
)
from services.process_service import ProcessService

##
# @file dashboard.py
# @brief Enrutador de API para el control de servicios y logs del sistema.
# @details Contiene los endpoints para arrancar, parar y monitorizar aplicaciones externas.
#

router = APIRouter(tags=["Dashboard"])


# =====================================================
# START SERVICE (REAL)
# =====================================================

@router.post("/start/{service}")
def start_service(service: str):
    """
    @brief Arranca un servicio del sistema.
    
    Lanza el subproceso correspondiente a la aplicación solicitada mediante el servicio de procesos
    y registra la acción en el historial de logs.
    
    @param service Nombre o identificador del servicio a arrancar (ej: 'calculator', 'browser').
    
    @return dict/bool Resultado de la operación devuelto por ProcessService.
    """
    result = ProcessService.start(service)
    add_log(service, f"START REQUEST -> {result}")
    return result


# =====================================================
# STOP SERVICE (REAL)
# =====================================================

@router.post("/stop/{service}")
def stop_service(service: str):
    """
    @brief Detiene un servicio del sistema en ejecución.
    
    Finaliza el proceso activo del servicio indicado y añade el evento al registro de logs.
    
    @param service Nombre o identificador del servicio a detener.
    
    @return dict/bool Resultado de la operación devuelto por ProcessService.
    """
    result = ProcessService.stop(service)
    add_log(service, f"STOP REQUEST -> {result}")
    return result


# =====================================================
# STATUS (OPCIONAL PERO RECOMENDADO)
# =====================================================

@router.get("/status")
def status():
    """
    @brief Obtiene el estado actual de todos los servicios.
    
    Consulta qué aplicaciones del sistema están activas (en ejecución) o detenidas en este momento.
    
    @return dict Diccionario con el estado estructurado de cada servicio registrado.
    """
    return ProcessService.status()


# =====================================================
# LOGS
# =====================================================

@router.get("/logs/{service}")
def logs(service: str):
    """
    @brief Recupera los logs específicos de un servicio.
    
    Obtiene el historial de acciones y comandos ejecutados relacionados con la aplicación solicitada.
    
    @param service Nombre o identificador del servicio a consultar.
    
    @return dict Contenedor con la lista de líneas de registro encontradas.
    """
    return {
        "logs": get_logs(service)
    }


# =====================================================
# CLEAR LOGS
# =====================================================

@router.delete("/logs/{service}")
def clear(service: str):
    """
    @brief Vacía el historial de logs de un servicio.
    
    Elimina todos los registros guardados en memoria o disco para reiniciar el historial de la app.
    
    @param service Nombre o identificador del servicio cuyo log se desea limpiar.
    
    @return dict Confirmación del estado de la limpieza (ej: {"status": "ok"}).
    """
    clear_logs(service)
    return {"status": "ok"}


# =====================================================
# ALL LOGS
# =====================================================

@router.get("/logs")
def all_logs():
    """
    @brief Recupera el historial completo de logs globales.
    
    Reúne los registros de todas las aplicaciones e interacciones del sistema en un solo volcado de datos.
    
    @return list/dict Lista completa de los eventos de log almacenados en el sistema.
    """
    return get_all_logs()