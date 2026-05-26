import requests
from bs4 import BeautifulSoup


## @file web_search.py
#  @brief Búsqueda web básica usando DuckDuckGo HTML.
#
#  Este módulo implementa una búsqueda simple sin API oficial,
#  extrayendo resultados desde la versión HTML de DuckDuckGo.
#
#  ⚠️ Nota:
#   - Es un método frágil (puede cambiar el HTML del sitio)
#   - Útil como fallback ligero sin dependencias externas de API


## @brief Realiza una búsqueda web básica.
#
#  Usa DuckDuckGo en modo HTML para obtener resultados
#  y extrae títulos de enlaces.
#
#  @param query Texto de búsqueda.
#  @param limit Número máximo de resultados.
#
#  @return str Lista de resultados separados por saltos de línea.
#  @retval "" Si ocurre un error o no hay resultados.
def web_search(query: str, limit: int = 3) -> str:
    """
    Busca información en DuckDuckGo HTML (fallback básico).
    """

    try:

        # =========================
        # PETICIÓN WEB
        # =========================

        url = (
            "https://html.duckduckgo.com/html/"
            f"?q={query}"
        )

        r = requests.get(url, timeout=10)

        # =========================
        # PARSEO HTML
        # =========================

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        results = []

        # =========================
        # EXTRACCIÓN RESULTADOS
        # =========================

        for a in soup.find_all(
            "a",
            class_="result__a",
            limit=limit
        ):

            text = a.get_text(strip=True)

            if text:
                results.append(text)

        # =========================
        # RESPUESTA FINAL
        # =========================

        return "\n".join(results)

    except Exception:

        return ""