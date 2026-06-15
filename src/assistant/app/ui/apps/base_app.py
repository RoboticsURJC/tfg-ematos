from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal


class BaseApp(QWidget):
    """
    Clase base para todas las apps del sistema.
    """

    open_assistant = pyqtSignal()
    close_app = pyqtSignal()

    def __init__(self, controller=None, engine=None):
        super().__init__()

        self.controller = controller
        self.engine = engine

        self.app_name = "base"

    # =========================
    # CICLO DE VIDA
    # =========================
    def on_open(self):
        """
        Llamado cuando la app se abre
        """
        pass

    def on_close(self):
        """
        Llamado cuando la app se cierra
        """
        pass

    # =========================
    # UTILIDADES
    # =========================
    def back(self):
        if self.controller:
            self.controller.go("launcher")
