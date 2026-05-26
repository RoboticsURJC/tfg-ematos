import requests


class WeatherService:
    """
    Clima basado en API tipo OpenWeather o backend propio.
    """

    def __init__(self, api_key=None, base_url="https://api.openweathermap.org/data/2.5"):
        self.api_key = api_key
        self.base_url = base_url

    def get_weather(self, city: str, lang="es"):
        if not self.api_key:
            return {
                "error": "API key no configurada"
            }

        r = requests.get(
            f"{self.base_url}/weather",
            params={
                "q": city,
                "appid": self.api_key,
                "lang": lang,
                "units": "metric"
            },
            timeout=10
        )

        r.raise_for_status()
        data = r.json()

        return {
            "city": data.get("name"),
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"]
        }
