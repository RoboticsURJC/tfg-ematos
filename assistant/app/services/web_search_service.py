import requests


class WebSearchService:
    """
    Servicio simple de búsqueda web (API externa o backend propio).
    """

    def __init__(self, endpoint="http://localhost:8001/search"):
        self.endpoint = endpoint

    def search(self, query: str, limit: int = 5):
        r = requests.get(
            self.endpoint,
            params={
                "q": query,
                "limit": limit
            },
            timeout=10
        )

        r.raise_for_status()
        return r.json().get("results", [])

    def summarize(self, query: str, llm):
        """
        Pipeline opcional: search + LLM resumen
        """
        results = self.search(query)

        context = "\n".join(
            f"- {r.get('title')} : {r.get('snippet')}"
            for r in results
        )

        prompt = f"""
        Resume la siguiente información de forma clara:

        {context}
        """

        return llm.ask(prompt)
