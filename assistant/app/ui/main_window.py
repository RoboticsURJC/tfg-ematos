from PyQt5.QtWidgets import QWidget, QStackedLayout, QVBoxLayout

from app.ui.screens.boot_screen import BootScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.register_screen import RegisterScreen
from app.ui.screens.launcher_screen import LauncherScreen
from app.ui.screens.assistant_screen import AssistantScreen
from app.ui.screens.error_screen import ErrorScreen

from app.core.logger import logger


class MainWindow(QWidget):

    def __init__(self, controller):
        super().__init__()

        logger.info(" -> Iniciando MainWindow")

        self.controller = controller

        self.setWindowTitle("Rojazz UI")
        self.setMinimumSize(900, 700)

        # =========================
        # STACK
        # =========================
        self.stack = QStackedLayout()

        self.boot_screen = BootScreen(controller)
        self.login_screen = LoginScreen(controller)
        self.register_screen = RegisterScreen(controller)
        self.launcher_screen = LauncherScreen(controller)
        self.assistant_screen = AssistantScreen(controller)
        self.error_screen = ErrorScreen(controller)

        self.stack.addWidget(self.boot_screen)
        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.register_screen)
        self.stack.addWidget(self.launcher_screen)
        self.stack.addWidget(self.assistant_screen)
        self.stack.addWidget(self.error_screen)

        root = QVBoxLayout()
        root.addLayout(self.stack)
        self.setLayout(root)

        # =========================
        # START SCREEN
        # =========================
        self.stack.setCurrentWidget(self.boot_screen)

        # Abrir login screen
        self.boot_screen.finished.connect(self.show_login)

    # =========================
    # NAVIGATION
    # =========================
    def show_boot(self):
        self.stack.setCurrentWidget(self.boot_screen)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_screen)

    def show_register(self):
        self.stack.setCurrentWidget(self.register_screen)

    def show_launcher(self):
        self.stack.setCurrentWidget(self.launcher_screen)

    def show_assistant(self):
        self.stack.setCurrentWidget(self.assistant_screen)

    def show_error(self):
        self.stack.setCurrentWidget(self.error_screen)
