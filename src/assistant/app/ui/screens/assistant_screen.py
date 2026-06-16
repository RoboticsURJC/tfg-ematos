# app/ui/apps/assistant/assistant_screen.py

"""
@file assistant_screen.py
@brief Interfaz de usuario para la interacción con el asistente de voz/IA.
@details Clase encargada de mostrar el estado actual del asistente (escuchando, 
procesando, inactivo) mientras el motor de IA está activo.
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from app.core.logger import logger

class AssistantScreen(QWidget):
    """
    @brief Pantalla visual para el asistente IA.
    @details Muestra al usuario feedback visual sobre el estado del motor de IA.
    """

    def __init__(self, engine):
        """
        @brief Inicializa la pantalla del asistente.
        @param engine Objeto que controla la lógica de la IA o el procesamiento de voz.
        """
        super().__init__()

        logger.info("[ASSISTANT SCREEN] Iniciando ventana Assistant Screen")

        self.engine = engine

        # Layout vertical para apilar etiquetas de estado
        layout = QVBoxLayout()

        self.title = QLabel(" Asistente activo")
        self.title.setAlignment(Qt.AlignCenter)
        # Sugerencia: Puedes añadir setStyleSheet aquí para mejorar la apariencia

        self.state = QLabel("Esperando orden...")
        self.state.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title)
        layout.addWidget(self.state)

        self.setLayout(layout)

    def set_state(self, text: str):
        """
        @brief Actualiza el texto de estado en la interfaz.
        @param text Mensaje que indica qué está haciendo el asistente (ej: "Escuchando...", "Pensando...").
        """
        self.state.setText(text)
        logger.info(f"[ASSISTANT SCREEN] Nuevo estado: {text}")