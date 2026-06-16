# app/core/game_router.py

from PyQt5.QtCore import QTimer
from app.ui.apps.games.memory_screen import MemoryScreen 
from app.ui.apps.games.word_search_screen import WordSearchScreen 
from app.ui.apps.games.find_differences_screen import FindDifferencesScreen 
from app.ui.apps.games.simon_says_screen import SimonSaysScreen
from app.core.logger import logger

##
# @file game_router.py
# @brief Enrutador lógico y gestor de pantallas para las aplicaciones de estimulación cognitiva (juegos).
# @details Controla la transición de ventanas dentro del contenedor Stack de PyQt5, activando e 
# inicializando los ciclos de juego correspondientes a las peticiones del robot.
#

class GameRouter:
    """
    @brief Clase encargada de enrutar y levantar las interfaces gráficas de los diferentes juegos.
    """

    def __init__(self, controller):
        """
        @brief Constructor del enrutador de juegos.
        
        @param controller Instancia del controlador principal del robot (Master Controller) que posee la referencia a la UI.
        """
        ## Referencia al controlador principal de la aplicación.
        self.controller = controller

    def open_game(self, game_id: str):
        """
        @brief Cambia la interfaz actual del robot e inicia el juego cognitivo solicitado de forma asíncrona.
        @details Extrae el widget contenedor (`stack`) de la UI, posiciona la pantalla objetivo en primer 
        plano y delega la ejecución del método `start()` del juego mediante un disparo único de QTimer.
        
        @note Se utiliza `QTimer.singleShot(0, ...)` para delegar el arranque del juego al siguiente ciclo 
        del bucle de eventos de Qt. Esto asegura que la pantalla se dibuje y renderice por completo en el 
        hilo principal antes de que la lógica pesada del juego comience a ejecutarse.
        
        @param game_id Identificador único textual del juego a abrir ('memory', 'word_search', 'simon_says', 'find_diferences').
        """
        ui = self.controller.ui
                 
        if not ui:
            logger.error("[GAME ROUTER] UI no disponible")
            return
        
        # --- Juego de Memoria (Parejas) ---
        if game_id == "memory":
            screen = ui.memory_screen
            ui.stack.setCurrentWidget(screen)
            QTimer.singleShot(0, screen.start)
            logger.info("[GAME ROUTER] Juego memory iniciado")
            return
            
        # --- Juego de Sopa de Letras ---
        if game_id == "word_search":
            screen = ui.word_search_screen
            ui.stack.setCurrentWidget(screen)
            QTimer.singleShot(0, screen.start)
            logger.info("[GAME ROUTER] Juego sopa de letras iniciado")
            return
            
        # --- Juego de Simón Dice ---
        if game_id == "simon_says":
            screen = ui.simon_says_screen
            ui.stack.setCurrentWidget(screen)
            QTimer.singleShot(0, screen.start)
            logger.info("[GAME ROUTER] Juego Simon Dice iniciado")
            return
        
        # --- Juego de Encuentra las Diferencias ---
        if game_id == "find_diferences":
            screen = ui.find_differences_screen
            ui.stack.setCurrentWidget(screen)
            QTimer.singleShot(0, screen.start)
            logger.info("[GAME ROUTER] Juego encuentra las dferencias iniciado")
            return
         
        logger.warning(f"[GAME ROUTER] Juego desconocido solicitado: {game_id}")