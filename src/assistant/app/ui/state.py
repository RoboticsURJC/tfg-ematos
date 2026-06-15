# app/ui/state.py

from PyQt5.QtCore import QObject, pyqtSignal


class UIState(QObject):
    """
    Estado global de la UI.

    Centraliza:
    - usuario activo
    - app abierta
    - pantalla actual
    - estado del sistema
    - voz/escucha
    - errores

    Todo conectado mediante señales Qt.
    """

    # =========================================================
    # SIGNALS
    # =========================================================

    user_changed = pyqtSignal(str)

    screen_changed = pyqtSignal(str)

    app_changed = pyqtSignal(str)

    status_changed = pyqtSignal(str)

    listening_changed = pyqtSignal(bool)

    speaking_changed = pyqtSignal(bool)

    loading_changed = pyqtSignal(bool)

    error_occurred = pyqtSignal(str)

    theme_changed = pyqtSignal(str)

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self):
        super().__init__()

        # =====================================================
        # USER
        # =====================================================

        self.current_user = None

        # =====================================================
        # UI
        # =====================================================

        self.current_screen = "boot"

        self.current_app = None

        self.current_theme = "dark"

        # =====================================================
        # ROBOT
        # =====================================================

        self.is_listening = False

        self.is_speaking = False

        self.is_loading = False

        # =====================================================
        # STATUS
        # =====================================================

        self.status_message = "Sistema iniciado"

        self.last_error = None

    # =========================================================
    # USER
    # =========================================================

    def set_user(self, user: str):

        self.current_user = user

        self.user_changed.emit(user)

    def clear_user(self):

        self.current_user = None

        self.user_changed.emit("")

    # =========================================================
    # SCREEN
    # =========================================================

    def set_screen(self, screen: str):

        self.current_screen = screen

        self.screen_changed.emit(screen)

    # =========================================================
    # APPS
    # =========================================================

    def open_app(self, app_name: str):

        self.current_app = app_name

        self.app_changed.emit(app_name)

    def close_app(self):

        self.current_app = None

        self.app_changed.emit("")

    # =========================================================
    # STATUS
    # =========================================================

    def set_status(self, message: str):

        self.status_message = message

        self.status_changed.emit(message)

    # =========================================================
    # LISTENING
    # =========================================================

    def set_listening(self, value: bool):

        self.is_listening = value

        self.listening_changed.emit(value)

    # =========================================================
    # SPEAKING
    # =========================================================

    def set_speaking(self, value: bool):

        self.is_speaking = value

        self.speaking_changed.emit(value)

    # =========================================================
    # LOADING
    # =========================================================

    def set_loading(self, value: bool):

        self.is_loading = value

        self.loading_changed.emit(value)

    # =========================================================
    # ERRORS
    # =========================================================

    def set_error(self, error_message: str):

        self.last_error = error_message

        self.error_occurred.emit(error_message)

    def clear_error(self):

        self.last_error = None

    # =========================================================
    # THEMES
    # =========================================================

    def set_theme(self, theme_name: str):

        self.current_theme = theme_name

        self.theme_changed.emit(theme_name)

    # =========================================================
    # RESET UI
    # =========================================================

    def reset(self):
        """
        Reinicia el estado completo.
        Muy útil al cerrar sesión.
        """

        self.current_user = None

        self.current_screen = "login"

        self.current_app = None

        self.is_listening = False

        self.is_speaking = False

        self.is_loading = False

        self.status_message = "Esperando usuario"

        self.last_error = None

        # signals

        self.user_changed.emit("")

        self.screen_changed.emit("login")

        self.app_changed.emit("")

        self.status_changed.emit(
            self.status_message
        )

        self.listening_changed.emit(False)

        self.speaking_changed.emit(False)

        self.loading_changed.emit(False)

    # =========================================================
    # DEBUG
    # =========================================================

    def dump_state(self):

        return {
            "user": self.current_user,
            "screen": self.current_screen,
            "app": self.current_app,
            "listening": self.is_listening,
            "speaking": self.is_speaking,
            "loading": self.is_loading,
            "status": self.status_message,
            "theme": self.current_theme,
            "error": self.last_error
        }
