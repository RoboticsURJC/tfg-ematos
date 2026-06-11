import subprocess
import shutil

from app.core.logger import logger


class SystemApps:

    APPS = {
        "notes": "internal:notes",
        "browser": ["firefox", "chromium", "chromium-browser"],
        "calendar": "internal:calendar",
        "calculator": ["galculator", "gnome-calculator", "calc"],
        "reminder": "internal:reminder",
        "games": "internal:games"
    }

    @classmethod
    def launch(cls, app_id):

        action = cls.APPS.get(app_id)

        if not action:
            logger.error(f"[SYSTEM APPS] Aplicación no registrada: {app_id}")
            return False

        # =========================
        # APPS INTERNAS (UI PYQT)
        # =========================
        if isinstance(action, str) and action.startswith("internal:"):
            return action   #  IMPORTANTE: NO ejecutamos subprocess

        # =========================
        # APPS DEL SISTEMA
        # =========================
        if isinstance(action, list):

            for app in action:

                if shutil.which(app):

                    try:
                        subprocess.Popen([app])
                        logger.info(f"[SYSTEM APP] Aplicación lanzada: {app}")
                        return True

                    except Exception as e:
                        logger.error(f"[SYSTEM APP] Error lanzando {app}: {e}")

            logger.error(f"[SYSTEM APP] No se encontró ninguna app válida para {app_id}")
            return False

        return False
