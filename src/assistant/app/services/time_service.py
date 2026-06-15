from datetime import datetime
import pytz


class TimeService:
    """
    Servicio de tiempo global con zonas horarias.
    """

    def get_time(self, timezone: str = "Europe/Madrid", format_24h=True):
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        if format_24h:
            return now.strftime("%H:%M:%S")
        else:
            return now.strftime("%I:%M:%S %p")

    def get_date(self, timezone: str = "Europe/Madrid"):
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        return now.strftime("%Y-%m-%d")

    def get_datetime(self, timezone: str = "Europe/Madrid"):
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A")
        }
