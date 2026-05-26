# app/core/app_registry.py

from app.ui.apps.weather_app import WeatherApp
from app.ui.apps.music_app import MusicApp
from app.ui.apps.camera_app import CameraApp
from app.ui.apps.browser_app import BrowserApp
from app.ui.apps.system_app import SystemApp


class AppRegistry:
    """
    Registro central de apps.
    """

    def __init__(self):

        self.apps = {}

    # =========================================================
    # REGISTER
    # =========================================================

    def register_defaults(self):

        self.register(
            "weather",
            WeatherApp
        )

        self.register(
            "music",
            MusicApp
        )

        self.register(
            "camera",
            CameraApp
        )

        self.register(
            "browser",
            BrowserApp
        )

        self.register(
            "system",
            SystemApp
        )

    # =========================================================
    # REGISTER APP
    # =========================================================

    def register(self, app_id, app_class):

        self.apps[app_id] = app_class

    # =========================================================
    # CREATE
    # =========================================================

    def create(self, app_id):

        if app_id not in self.apps:
            raise ValueError(
                f"App no registrada: {app_id}"
            )

        return self.apps[app_id]()

    # =========================================================
    # LIST
    # =========================================================

    def list_apps(self):

        return list(self.apps.keys())
