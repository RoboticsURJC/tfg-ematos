# app/ui/apps/loading/loading_screen.py

"""
@file loading_screen.py
@brief Pantalla de espera (Loading Screen) con animación de puntos.
@details Proporciona una interfaz simple de retroalimentación para indicar al 
usuario que el sistema está procesando una tarea en segundo plano.
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from app.core.logger import logger

class LoadingScreen(QWidget):
    """
    @brief Pantalla de carga con animación simple.
    @details Utiliza un QTimer para alternar el número de puntos al final del texto.
    """

    def __init__(self, text: str = "Cargando"):
        """
        @brief Inicializa la pantalla de carga.
        @param text Texto base a mostrar (por defecto "Cargando").
        """
        super().__init__()

        logger.info(f"[LOADING SCREEN] Iniciando. Texto base: {text}")

        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)

        self.base_text = text
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 28px; font-weight: 800; color: #5a3300;")

        layout.addWidget(self.label)
        self.setLayout(layout)

        # Estado del contador de puntos
        self.dots = 0

        # Temporizador para la animación
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(400)

    def animate(self):
        """
        @brief Actualiza el texto añadiendo puntos cíclicamente.
        """
        self.dots = (self.dots + 1) % 4
        self.label.setText(self.base_text + "." * self.dots)

    def closeEvent(self, event):
        """
        @brief Detiene el temporizador al cerrar la pantalla para evitar fugas de memoria.
        """
        self.timer.stop()
        super().closeEvent(event)