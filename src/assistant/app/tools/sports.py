 
# TOOLS SPORTS 

"""
@file sports.py
@brief Consulta de resultados de fútbol mediante football-data.org (plan gratuito).
"""

import os
import requests
from datetime import datetime, timedelta
from app.core.logger import logger

FOOTBALL_DATA_TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")
BASE_URL = "https://api.football-data.org/v4"

# Mapeo simple de nombres de equipos en español -> nombres/IDs que usa la API.
# football-data.org busca mejor por nombre parcial en inglés, así que mapeamos
# los más habituales para no depender de que el usuario diga el nombre exacto.
EQUIPOS = {
    "real madrid": "Real Madrid",
    "madrid": "Real Madrid",
    "barcelona": "Barcelona",
    "barça": "Barcelona",
    "barca": "Barcelona",
    "atlético": "Atlético Madrid",
    "atletico": "Atlético Madrid",
    "atleti": "Atlético Madrid",
    "sevilla": "Sevilla",
    "valencia": "Valencia",
    "athletic": "Athletic Club",
    "betis": "Real Betis",
}


def _normalizar_equipo(texto):
    """
    @brief Detecta el nombre de equipo mencionado en el texto del usuario.
    @param texto Texto en minúsculas.
    @return str|None Nombre normalizado del equipo o None si no se reconoce.
    """
    for clave, nombre in EQUIPOS.items():
        if clave in texto:
            return nombre
    return None


def get_resultado_equipo(texto):
    """
    @brief Busca el partido más reciente (jugado o programado) de un equipo mencionado en el texto.
    @param texto Transcripción del usuario, en minúsculas.
    @return str Frase lista para TTS con el resultado, o mensaje de error/aviso.
    """
    if not FOOTBALL_DATA_TOKEN:
        logger.warning("[SPORTS] FOOTBALL_DATA_TOKEN no configurado")
        return ""

    equipo = _normalizar_equipo(texto)
    if not equipo:
        return ""

    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}

    try:
        # 1. Buscar el ID del equipo
        r = requests.get(
            f"{BASE_URL}/teams",
            headers=headers,
            params={"name": equipo},
            timeout=10
        )
        if r.status_code != 200:
            logger.error(f"[SPORTS] búsqueda equipo status={r.status_code}")
            return ""

        teams = r.json().get("teams", [])
        if not teams:
            return f"No he encontrado al equipo {equipo} en mi base de datos."

        team_id = teams[0]["id"]

        # 2. Pedir los partidos del equipo, ventana de -7 a +7 días
        hoy = datetime.now().date()
        date_from = (hoy - timedelta(days=7)).isoformat()
        date_to = (hoy + timedelta(days=7)).isoformat()

        r = requests.get(
            f"{BASE_URL}/teams/{team_id}/matches",
            headers=headers,
            params={"dateFrom": date_from, "dateTo": date_to},
            timeout=10
        )
        if r.status_code != 200:
            logger.error(f"[SPORTS] búsqueda partidos status={r.status_code}")
            return ""

        matches = r.json().get("matches", [])
        if not matches:
            return f"No encuentro partidos recientes ni próximos de {equipo}."

        # Separar jugados de pendientes, quedarnos con el más relevante
        jugados = [m for m in matches if m["status"] == "FINISHED"]
        pendientes = [m for m in matches if m["status"] in ("SCHEDULED", "TIMED")]

        if jugados:
            ultimo = sorted(jugados, key=lambda m: m["utcDate"])[-1]
            local = ultimo["homeTeam"]["name"]
            visitante = ultimo["awayTeam"]["name"]
            gl = ultimo["score"]["fullTime"]["home"]
            gv = ultimo["score"]["fullTime"]["away"]
            fecha = datetime.fromisoformat(
                ultimo["utcDate"].replace("Z", "+00:00")
            ).strftime("%d/%m")
            return f"El {fecha}, {local} {gl} - {gv} {visitante}."

        if pendientes:
            proximo = sorted(pendientes, key=lambda m: m["utcDate"])[0]
            local = proximo["homeTeam"]["name"]
            visitante = proximo["awayTeam"]["name"]
            fecha_dt = datetime.fromisoformat(
                proximo["utcDate"].replace("Z", "+00:00")
            )
            fecha = fecha_dt.strftime("%d/%m a las %H:%M")
            return f"Aún no se ha jugado. El próximo partido es {local} contra {visitante}, el {fecha}."

        return ""

    except Exception as e:
        logger.error(f"[SPORTS] error: {e}")
        return ""
