# app/ui/apps/error/error_screen.py

"""
@file error_screen.py
@brief Pantalla de notificación de errores del sistema.
@details Interfaz simple para informar al usuario sobre excepciones o fallos 
críticos durante la ejecución de la aplicación.
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from app.core.logger import logger

class ErrorScreen(QWidget):
    """
    @brief Pantalla de error genérica.
    @details Se utiliza para capturar y mostrar mensajes de error de forma 
    amigable en lugar de cerrar la aplicación abruptamente.
    """

    def __init__(self, controller, message="Error"):
        """
        @brief Inicializa la pantalla de error.
        @param controller Referencia al controlador principal.
        @param message Mensaje descriptivo del error ocurrido.
        """
        super().__init__()

        logger.info(f"[ERROR SCREEN] Iniciando ventana. Mensaje: {message}")

        self.controller = controller

        # Layout vertical para centrar el mensaje
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # Título del error
        self.label = QLabel(" Algo salió mal")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 32px; font-weight: 900; color: #b91c1c;")

        # Detalle del mensaje de error
        self.detail = QLabel(message)
        self.detail.setAlignment(Qt.AlignCenter)
        self.detail.setWordWrap(True)  # Permite saltos de línea si el mensaje es largo
        self.detail.setStyleSheet("font-size: 20px; color: #4b5563;")

        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(self.detail)
        layout.addStretch()

        self.setLayout(layout)

    def set_message(self, message: str):
        """
        @brief Actualiza el mensaje de error dinámicamente.
        @param message Nuevo texto de error.
        """
        self.detail.setText(message)
        logger.info(f"[ERROR SCREEN] Mensaje actualizado: {message}")