# app/ui/app_controller.py

"""
@file app_controller.py
@brief Orquestador central de la interfaz de usuario y navegación.
@details Gestiona el flujo de pantallas mediante QStackedWidget, coordina la 
comunicación con el hardware (FaceDisplay) y el motor de IA (AssistantEngine), 
y centraliza la lógica de estados en el sistema.
"""

from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtCore import QObject, pyqtSignal


class AppController(QObject):
    """
    @brief Orquestador central de navegación y estado de la aplicación.
    @details Actúa como el controlador principal en el patrón MVC, gestionando 
    la transición entre vistas y facilitando la comunicación entre los componentes 
    críticos del sistema (UI, Hardware, IA).
    
    @attr user_logged Señal emitida cuando un usuario se autentica correctamente.
    @attr app_changed Señal emitida al realizar una transición entre aplicaciones.
    """

    # señales globales
    user_logged = pyqtSignal(str)
    app_changed = pyqtSignal(str)

    # =========================
    # INIT
    # =========================
    def __init__(self, display=None, engine=None):
        
        """
        @brief Inicializa el controlador de aplicaciones.
        @param display Objeto de hardware (FaceDisplay) para control visual del robot.
        @param engine Objeto de motor de IA (AssistantEngine) para procesamiento.
        """
        
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
        @brief Registra un widget de pantalla en el sistema de navegación.
        @param name Identificador único de la pantalla (key).
        @param widget Instancia del widget (QWidget) a añadir al stack.
        """
        self.screens[name] = widget
        self.stack.addWidget(widget)

    # =========================
    # NAVEGACIÓN
    # =========================
    def go(self, name: str):
        """
        @brief Realiza la transición a la pantalla especificada.
        @param name Identificador de la pantalla registrada.
        @throws ValueError Si el nombre de la pantalla no está registrado.
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
        @brief Ejecuta el flujo inicial del sistema.
        @details Lanza la pantalla de arranque (boot) y establece la conexión 
        de señales para la transición automática a login.
        """

        self.go("boot")

        boot = self.screens.get("boot")
        if hasattr(boot, "finished"):
            boot.finished.connect(self._on_boot_finished)

    def _on_boot_finished(self):
        """@brief Callback interno al finalizar la secuencia de arranque."""
        self.go("login")

    # =========================
    # LOGIN HANDLING
    # =========================
    def on_user_authenticated(self, user: str):
        """
        @brief Gestiona la lógica posterior a una autenticación exitosa.
        @details Notifica al display, al motor de IA y redirige al lanzador principal.
        @param user Nombre del usuario autenticado.
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
        @brief Navega a una aplicación específica desde el launcher.
        @param app_name Identificador de la aplicación destino.
        """

        if self.display:
            self.display.set_estado(f"App: {app_name}")

        self.app_changed.emit(app_name)

        self.go(app_name)

    # =========================
    # ASISTENTE
    # =========================
    def open_assistant(self):
        """@brief Realiza la transición a la pantalla del asistente virtual."""
        self.go("assistant")

        if self.display:
            self.display.set_estado("Asistente activo")

    # =========================
    # ERROR GLOBAL
    # =========================
    def error(self, message: str):
        """
        @brief Fuerza la transición a la pantalla de error global.
        @param message Mensaje descriptivo del error a mostrar en la interfaz.
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
        @brief Devuelve el contenedor de pantallas para su integración en el main.
        @return QStackedWidget principal de la aplicación.
        """
        return self.stack