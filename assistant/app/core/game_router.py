# app/core/game_router.py

from PyQt5.QtCore import QTimer
from app.ui.apps.games.memory_screen import MemoryScreen 
from app.ui.apps.games.word_search_screen import WordSearchScreen 
from app.core.logger import logger

class GameRouter:

    def __init__(self, controller):
        self.controller = controller

    def open_game(self, game_id: str):
        
        ui = self.controller.ui
                 
        if not ui:
           logger.error("[GAME ROUTER] UI no disponible")
           return
        
        if game_id == "memory":
            screen = ui.memory_screen
            ui.stack.setCurrentWidget(screen)
            QTimer.singleShot(0, screen.start)
            
            logger.info("[GAME ROUTER] Juego memory iniciado")
            return
            
            
        if game_id == "word_search":
            screen = ui.word_search_screen
            ui.stack.setCurrentWidget(screen)
            QTimer.singleShot(0, screen.start)
            
            logger.info("[GAME ROUTER] Juego sopa de letras iniciado")
            return
         
        logger.warning("[GAME ROUTER] Juego desconocido")

            
        # ~ screen = self.games.get(game_id)

        # ~ if not screen:
            # ~ logger.info(f"[GAME ROUTER] Juego no encontrado: {game_id}")
            # ~ return

        # ~ #  activar juego
        # ~ screen.start()
        # ~ logger.info(f"[GAME ROUTER] Activando juego: {game_id}")


        # ~ # cambiar pantalla Qt
        # ~ self.ui.stack.setCurrentWidget(screen)
