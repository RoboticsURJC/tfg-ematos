# import sys
# import logging

# from PyQt5.QtWidgets import QApplication

# from app.ui.face_client import FaceClient
# from app.ui.theme import MAIN_STYLE
# from app.core.assistant_engine import AssistantEngine

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("main")


# def main():

#     app = QApplication(sys.argv)

#     app.setStyle("Fusion")
#     app.setStyleSheet(MAIN_STYLE)

#     engine = None

#     def on_user(user):
#         engine.on_user(user)

#     client = FaceClient(on_user)

#     engine = AssistantEngine(client.display)

#     client.show()

#     sys.exit(app.exec_())


# if __name__ == "__main__":
#     main()
from PyQt5.QtWidgets import QWidget, QStackedLayout, QVBoxLayout

from app.ui.screens.boot_screen import BootScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.launcher_screen import LauncherScreen
from app.ui.screens.assistant_screen import AssistantScreen
from app.ui.screens.error_screen import ErrorScreen
from app.core.logger import logger


class MainWindow(QWidget):

    def __init__(self, controller):
        super().__init__()

        logger.info(" -> Iniciando Pantalla Principal")


        self.controller = controller

        self.setWindowTitle("Robot UI")

        # =========================
        # STACK DE PANTALLAS
        # =========================
        self.stack = QStackedLayout()

        self.boot_screen = BootScreen(controller)
        self.login_screen = LoginScreen(controller)
        self.launcher_screen = LauncherScreen(controller)
        self.assistant_screen = AssistantScreen(controller)
        self.error_screen = ErrorScreen(controller)

        self.stack.addWidget(self.boot_screen)
        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.launcher_screen)
        self.stack.addWidget(self.assistant_screen)
        self.stack.addWidget(self.error_screen)

        # =========================
        # LAYOUT ROOT (IMPORTANTE)
        # =========================
        root = QVBoxLayout()
        root.addLayout(self.stack)
        self.setLayout(root)

        # pantalla inicial
        self.stack.setCurrentWidget(self.boot_screen)
        

    # =========================
    # NAVEGACIÓN
    # =========================
    def show_boot(self):
        self.stack.setCurrentWidget(self.boot_screen)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_screen)

    def show_launcher(self):
        self.stack.setCurrentWidget(self.launcher_screen)

    def show_assistant(self):
        self.stack.setCurrentWidget(self.assistant_screen)

    def show_error(self):
        self.stack.setCurrentWidget(self.error_screen)
