from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtCore import QObject, pyqtSignal


class AppController(QObject):
    """
    Orquestador de pantallas UI.
    Maneja navegación tipo sistema operativo kiosko.
    """

    # señales globales
    user_logged = pyqtSignal(str)
    app_changed = pyqtSignal(str)

    # =========================
    # INIT
    # =========================
    def __init__(self, display=None, engine=None):
        super().__init__()

        self.display = display      # FaceDisplay (robot físico)
        self.engine = engine        # AssistantEngine (IA)

        self.stack = QStackedWidget()

        self.screens = {}
        self.current_user = None

    # =========================
    # REGISTRO DE PANTALLAS
    # =========================
    def register(self, name: str, widget):
        """
        Añade una pantalla al sistema
        """
        self.screens[name] = widget
        self.stack.addWidget(widget)

    # =========================
    # NAVEGACIÓN
    # =========================
    def go(self, name: str):
        """
        Cambia de pantalla
        """

        if name not in self.screens:
            raise ValueError(f"Screen '{name}' no registrada")

        widget = self.screens[name]
        self.stack.setCurrentWidget(widget)

        # sincronización visual del robot
        if self.display:
            self.display.set_estado(f"Modo: {name}")

        self.app_changed.emit(name)

    # =========================
    # BOOT FLOW
    # =========================
    def start(self):
        """
        Flujo inicial del sistema
        """

        self.go("boot")

        boot = self.screens.get("boot")
        if hasattr(boot, "finished"):
            boot.finished.connect(self._on_boot_finished)

    def _on_boot_finished(self):
        self.go("login")

    # =========================
    # LOGIN HANDLING
    # =========================
    def on_user_authenticated(self, user: str):
        """
        Llamado desde login_screen
        """

        self.current_user = user

        if self.display:
            self.display.set_user(user)
            self.display.set_estado(f"Hola {user}")

        if self.engine:
            self.engine.on_user(user)

        self.user_logged.emit(user)

        self.go("launcher")

    # =========================
    # ABRIR APP
    # =========================
    def open_app(self, app_name: str):
        """
        Navega a una app del launcher
        """

        if self.display:
            self.display.set_estado(f"App: {app_name}")

        self.app_changed.emit(app_name)

        self.go(app_name)

    # =========================
    # ASISTENTE
    # =========================
    def open_assistant(self):
        self.go("assistant")

        if self.display:
            self.display.set_estado("Asistente activo")

    # =========================
    # ERROR GLOBAL
    # =========================
    def error(self, message: str):
        """
        Fuerza pantalla de error
        """

        err = self.screens.get("error")

        if err and hasattr(err, "set_message"):
            err.set_message(message)

        if self.display:
            self.display.set_estado("ERROR")

        self.go("error")

    # =========================
    # UTIL
    # =========================
    def widget(self):
        """
        Devuelve el stack para meterlo en main.py
        """
        return self.stack