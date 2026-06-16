# app/ui/apps/base_app.py

"""
@file base_app.py
@brief Clase base abstracta para las aplicaciones del sistema.
@details Define la interfaz obligatoria para la integración de aplicaciones dentro 
del controlador principal, asegurando un ciclo de vida consistente.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

class BaseApp(QWidget):
    """
    @brief Clase base para todas las aplicaciones del sistema.
    @details Hereda de QWidget para proporcionar capacidades gráficas y define
    señales de comunicación necesarias para el gestor de ventanas/controller.
    """

    ## Señal emitida para solicitar la apertura del asistente de voz/IA
    open_assistant = pyqtSignal()
    
    ## Señal emitida para solicitar el cierre de la aplicación actual
    close_app = pyqtSignal()

    def __init__(self, controller=None, engine=None):
        """
        @brief Inicializa la aplicación base.
        @param controller Referencia al controlador del sistema (navegación).
        @param engine Referencia al motor de lógica o servicios compartidos.
        """
        super().__init__()

        self.controller = controller
        self.engine = engine
        self.app_name = "base"

    # =========================
    # CICLO DE VIDA
    # =========================
    def on_open(self):
        """
        @brief Hook de ciclo de vida: llamado automáticamente cuando la app se abre.
        @details Ideal para iniciar temporizadores, refrescar datos o resetear el estado.
        """
        pass

    def on_close(self):
        """
        @brief Hook de ciclo de vida: llamado automáticamente cuando la app se cierra.
        @details Ideal para detener procesos, limpiar recursos o guardar estados temporales.
        """
        pass

    # =========================
    # UTILIDADES
    # =========================
    def back(self):
        """
        @brief Método de navegación para volver al lanzador principal (launcher).
        """
        if self.controller:
            self.controller.go("launcher")