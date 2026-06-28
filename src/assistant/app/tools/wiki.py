
"""
@file wiki.py
@brief Consulta resúmenes de Wikipedia en español (API REST oficial, gratuita, sin key).
"""

import requests
from app.core.logger import logger

WIKI_API = "https://es.wikipedia.org/api/rest_v1/page/summary/"
WIKI_SEARCH = "https://es.wikipedia.org/w/api.php"

# Wikipedia exige un User-Agent identificativo en sus políticas de uso de la
# API. Sin esto, en ocasiones la respuesta es una página de bloqueo/aviso en
# HTML en vez del JSON esperado, lo que provoca errores como
# "Expecting value: line 1 column 1" al intentar parsear con r.json().
HEADERS = {
    "User-Agent": "AsistenteRobotico/1.0 (proyecto personal; contacto: tu_email@ejemplo.com)"
}


def _buscar_titulo(query):
    """
    @brief Busca el título de artículo más relevante en Wikipedia para una consulta libre.
    @param query Texto de búsqueda (ej: "Rosalía cantante").
    @return str|None Título exacto del artículo, o None si no hay resultados.
    """
    try:
        r = requests.get(
            WIKI_SEARCH,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1
            },
            headers=HEADERS,
            timeout=10
        )

        if r.status_code != 200:
            logger.warning(f"[WIKI] búsqueda status={r.status_code}")
            return None

        try:
            data = r.json()
        except ValueError:
            # La respuesta no es JSON (bloqueo, redirección, mantenimiento...).
            logger.warning(
                f"[WIKI] respuesta no-JSON en búsqueda, primeros 200 chars: {r.text[:200]!r}"
            )
            return None

        resultados = data.get("query", {}).get("search", [])
        if not resultados:
            return None
        return resultados[0]["title"]

    except requests.RequestException as e:
        logger.error(f"[WIKI] error de red en búsqueda: {e}")
        return None
    except Exception as e:
        logger.error(f"[WIKI] error inesperado en búsqueda: {e}")
        return None


def get_resumen(query):
    """
    @brief Obtiene un resumen breve de Wikipedia para una persona, lugar o tema.
    @param query Texto libre, ej. "quién es Rosalía" o "Torre Eiffel".
    @return str Resumen narrable por voz, o cadena vacía si no se encuentra nada.
    """
    titulo = _buscar_titulo(query)
    if not titulo:
        return ""

    try:
        r = requests.get(
            WIKI_API + requests.utils.quote(titulo),
            headers=HEADERS,
            timeout=10
        )

        if r.status_code != 200:
            logger.warning(f"[WIKI] resumen status={r.status_code} para '{titulo}'")
            return ""

        try:
            data = r.json()
        except ValueError:
            logger.warning(
                f"[WIKI] respuesta no-JSON en resumen, primeros 200 chars: {r.text[:200]!r}"
            )
            return ""

        # Páginas de desambiguación no traen un resumen útil
        if data.get("type") == "disambiguation":
            return ""

        extracto = data.get("extract", "")
        if not extracto:
            return ""

        # Limitar longitud para que sea cómodo de escuchar por voz
        frases = extracto.split(". ")
        resumen = ". ".join(frases[:3])
        if not resumen.endswith("."):
            resumen += "."
        return resumen

    except requests.RequestException as e:
        logger.error(f"[WIKI] error de red en resumen: {e}")
        return ""
    except Exception as e:
        logger.error(f"[WIKI] error inesperado en resumen: {e}")
        return ""
