from app.core.app_registry import AppRegistry
from app.core.assistant_engine import AssistantEngine
from app.core.session_manager import SessionManager
from app.core.state_machine import StateMachine
from app.ui.display import FaceDisplay
from app.ui.state import UIState

print(" ---------- Iniciando Robot controller -------------")


class RobotController:

    def __init__(self):

        self.ui = None  

        self.state_machine = StateMachine()
        self.session = SessionManager()

        self.registry = AppRegistry()
        self.registry.register_defaults()

        self.ui_state = UIState()

        self.display = FaceDisplay()
        self.display.start()

        self.assistant = AssistantEngine(
            ui_state=self.ui_state,
            face_display=self.display
        )

    # =========================================================
    # UI CONNECTION (CLAVE)
    # =========================================================
    def set_ui(self, ui):
        self.ui = ui

    # =========================================================
    # START SYSTEM
    # =========================================================
    def start(self):

        self.boot()

        if self.ui:
            self.ui.show_boot()

    # =========================================================
    # BOOT
    # =========================================================
    def boot(self):

        self.state_machine.set_state(StateMachine.BOOT)

        self.display.set_estado("Iniciando sistema")

    # =========================================================
    # LOGIN
    # =========================================================
    def login(self, username):

        self.session.login(username)
        self.ui_state.set_user(username)

        self.state_machine.set_state(StateMachine.HOME)

        # ~ self.display.set_user(username)
        self.display.set_estado(f"Hola {username}")

        self.assistant.set_user(username)
        self.assistant.start()

        if self.ui:
            self.ui.launcher_screen.set_user(username)
            self.ui.show_launcher()

    # =========================================================
    # LOGOUT
    # =========================================================
    def logout(self):

        self.session.logout()
        self.ui_state.reset()

        self.display.set_user(None)
        self.display.set_estado("Sesión cerrada")

        if self.ui:
            self.ui.show_login()

    # =========================================================
    # APPS
    # =========================================================
    def open_app(self, app_name):

        self.ui_state.open_app(app_name)
        self.state_machine.set_state(StateMachine.APP)

        self.display.set_estado(f"App: {app_name}")

    def close_app(self):

        self.ui_state.close_app()
        self.state_machine.set_state(StateMachine.HOME)

        if self.ui:
            self.ui.show_launcher()

    # =========================================================
    # SHUTDOWN
    # =========================================================
    def shutdown(self):

        self.state_machine.set_state(StateMachine.SHUTDOWN)

        self.assistant.stop()

        self.display.set_estado("Apagando...")

        self.display.stop()

        if self.ui:
            self.ui.close()
