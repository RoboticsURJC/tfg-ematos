import requests


## @file weather.py
#  @brief Utilidades meteorológicas usando Open-Meteo.
#
#  Este módulo permite:
#   - buscar coordenadas de ciudades
#   - consultar clima actual
#   - devolver información simplificada


## @brief Obtiene el clima actual de una ciudad.
#
#  Utiliza:
#   - Open-Meteo Geocoding API
#   - Open-Meteo Forecast API
#
#  Flujo:
#   1. Buscar coordenadas de la ciudad
#   2. Consultar clima actual
#   3. Generar respuesta amigable
#
#  @param city Nombre de la ciudad.
#
#  @return str Texto descriptivo del clima.
#
#  @retval str Información meteorológica actual.
#  @retval str Mensaje de error si falla la búsqueda.
def get_weather(city: str = "Madrid") -> str:
    """
    Devuelve el clima actual de una ciudad usando Open-Meteo.
    """

    try:

        # =========================
        # GEOLOCALIZACIÓN
        # =========================

        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}&count=1"
        ).json()

        # Ciudad no encontrada
        if "results" not in geo:
            return "No he podido encontrar esa ciudad."

        # Coordenadas
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        # =========================
        # CONSULTA METEO
        # =========================

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lon}"
            f"&current_weather=true"
        ).json()

        # Datos principales
        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]

        # =========================
        # RESPUESTA
        # =========================

        return (
            f"En {city} ahora hay "
            f"{temp}°C y viento de {wind} km/h"
        )

    except Exception:

        return (
            "No he podido obtener el clima "
            "en este momento."
        )