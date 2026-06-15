import os
import json


class Config:

    _instance = None
    _data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):

        #  sube desde app/core -> project root
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        config_path = os.path.join(base_dir, "config", "config.json")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config no encontrado: {config_path}")

        with open(config_path, "r") as f:
            self._data = json.load(f)

    # =========================
    # ACCESSORS
    # =========================

    def get(self, key, default=None):
        return self._data.get(key, default)

    def server(self):
        return self._data.get("server", {})

    def recognition_url(self):
        return self.server().get("recognition_url")

    def llm_url(self):
        return self.server().get("llm_url")
