# app/core/session_manager.py

import json
import os
import time


class SessionManager:
    """
    Gestiona:
    - usuario activo
    - login/logout
    - sesiones
    - persistencia básica
    """

    def __init__(self, data_path=None):

        base = os.path.dirname(
            os.path.abspath(__file__)
        )

        if data_path is None:
            data_path = os.path.join(
                base,
                "..",
                "data",
                "session.json"
            )

        self.data_path = data_path

        self.current_user = None

        self.login_time = None

        self.load()

    # =========================================================
    # LOGIN
    # =========================================================

    def login(self, username):

        self.current_user = username

        self.login_time = time.time()

        self.save()

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(self):

        self.current_user = None

        self.login_time = None

        self.save()

    # =========================================================
    # STATE
    # =========================================================

    @property
    def is_logged(self):

        return self.current_user is not None

    # =========================================================
    # SAVE
    # =========================================================

    def save(self):

        try:

            os.makedirs(
                os.path.dirname(self.data_path),
                exist_ok=True
            )

            data = {
                "current_user": self.current_user,
                "login_time": self.login_time
            }

            with open(self.data_path, "w") as f:
                json.dump(data, f, indent=4)

        except Exception as e:

            print("SESSION SAVE ERROR:", e)

    # =========================================================
    # LOAD
    # =========================================================

    def load(self):

        if not os.path.exists(self.data_path):
            return

        try:

            with open(self.data_path, "r") as f:
                data = json.load(f)

            self.current_user = data.get(
                "current_user"
            )

            self.login_time = data.get(
                "login_time"
            )

        except Exception as e:

            print("SESSION LOAD ERROR:", e)
