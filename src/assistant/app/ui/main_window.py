# app/ui/main_window.py

"""
@file main_window.py
@brief Ventana principal y contenedor raíz de la interfaz de usuario.
@details Gestiona el despliegue y navegación de todas las pantallas del sistema 
mediante un QStackedLayout. Actúa como el punto de entrada visual, centralizando 
el registro de aplicaciones y la lógica de transiciones.
"""

from PyQt5.QtWidgets import QWidget, QStackedLayout, QVBoxLayout
from PyQt5.QtCore import pyqtSignal 

from app.ui.screens.boot_screen import BootScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.register_screen import RegisterScreen
from app.ui.screens.launcher_screen import LauncherScreen
from app.ui.screens.assistant_screen import AssistantScreen
from app.ui.screens.error_screen import ErrorScreen
from app.ui.apps.notes.note_screen import NotesScreen
from app.ui.apps.calendar.calendar_screen import CalendarScreen
from app.ui.apps.reminder.reminder_screen import ReminderScreen
from app.ui.apps.games.games_screen import GamesScreen
from app.ui.apps.games.memory_screen import MemoryScreen
from app.ui.apps.games.word_search_screen import WordSearchScreen
from app.ui.apps.proactive.proactive_screen import ProactiveScreen
from app.ui.apps.games.find_differences_screen import FindDifferencesScreen 
from app.ui.apps.games.simon_says_screen import SimonSaysScreen
from app.ui.apps.browser.browser_screen import BrowserScreen
from app.ui.apps.settings.settings_screen import SettingsScreen

from app.core.logger import logger



class MainWindow(QWidget):
    
    """
    @brief Ventana principal de la aplicación.
    @details Mantiene una pila (stack) con todos los widgets de pantalla, facilitando
    la conmutación rápida entre modos (login, launcher, apps, juegos). 
    Incluye lógica especializada para la gestión de pantallas dinámicas (proactivas).
    
    @attr show_proactive_signal Señal para invocar una pantalla de sugerencia proactiva.
    """

    show_proactive_signal = pyqtSignal(object)
    refresh_reminders_signal = pyqtSignal()
    refresh_calendar_signal = pyqtSignal()

    def __init__(self, controller):
        
        """
        @brief Inicializa la ventana, instancia todas las pantallas y las registra en el stack.
        @param controller El controlador central de la aplicación.
        """
        
        super().__init__()

        logger.info("[MAIN WINDOW] Iniciando Ventanas")

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
        self.note_screen = NotesScreen(controller)
        self.calendar_screen = CalendarScreen(controller)
        self.reminder_screen = ReminderScreen(controller)
        self.games_screen = GamesScreen(controller)
        self.memory_screen = MemoryScreen(controller)
        self.word_search_screen = WordSearchScreen(controller)
        self.find_differences_screen = FindDifferencesScreen(controller)
        self.simon_says_screen = SimonSaysScreen(controller)
        self.browser_screen = BrowserScreen(controller)
        self.settings_screen = SettingsScreen(controller)


        self.stack.addWidget(self.boot_screen)
        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.register_screen)
        self.stack.addWidget(self.launcher_screen)
        self.stack.addWidget(self.assistant_screen)
        self.stack.addWidget(self.error_screen)
        self.stack.addWidget(self.note_screen)
        self.stack.addWidget(self.calendar_screen)
        self.stack.addWidget(self.reminder_screen)
        self.stack.addWidget(self.games_screen)
        self.stack.addWidget(self.memory_screen)
        self.stack.addWidget(self.word_search_screen)
        self.stack.addWidget(self.find_differences_screen)
        self.stack.addWidget(self.simon_says_screen)
        self.stack.addWidget(self.browser_screen)
        self.stack.addWidget(self.settings_screen)
        

        root = QVBoxLayout()
        root.addLayout(self.stack)
        self.setLayout(root)

        # =========================
        # START SCREEN
        # =========================
        self.stack.setCurrentWidget(self.boot_screen)

        # Abrir login screen
        self.boot_screen.finished.connect(self.show_login)

        # Conectar señal de proactividad
        self.show_proactive_signal.connect(self._show_proactive_slot)

    # =========================
    # NAVIGATION
    # =========================
    def show_boot(self):
        """@brief Cambia a la pantalla de inicio (boot)."""
        self.stack.setCurrentWidget(self.boot_screen)

    def show_login(self):
        """@brief Cambia a la pantalla de login."""
        self.stack.setCurrentWidget(self.login_screen)

    def show_register(self):
        """@brief Cambia a la pantalla de register."""
        self.stack.setCurrentWidget(self.register_screen)

    def show_launcher(self):
        """@brief Cambia a la pantalla de launcher."""
        self.stack.setCurrentWidget(self.launcher_screen)

    def show_assistant(self):
        """@brief Cambia a la pantalla de assistant."""        
        self.stack.setCurrentWidget(self.assistant_screen)

    def show_error(self):
        """@brief Cambia a la pantalla de error."""        
        self.stack.setCurrentWidget(self.error_screen)
        
    def show_notes(self):
        self.stack.setCurrentWidget(self.note_screen)
     
    def show_calendar(self):
        """@brief Cambia a la pantalla de calendar."""                
        self.stack.setCurrentWidget(self.calendar_screen)
        
    def show_reminder(self):
        """@brief Cambia a la pantalla de reminder."""        
        self.stack.setCurrentWidget(self.reminder_screen)
        
    def show_games(self):
        """@brief Cambia a la pantalla de games."""        
        self.stack.setCurrentWidget(self.games_screen)
                
    def show_memory(self):
        """@brief Cambia a la pantalla de memory."""        
        self.stack.setCurrentWidget(self.memory_screen)

    def show_word_search(self):
        """@brief Cambia a la pantalla de word search."""        
        self.stack.setCurrentWidget(self.word_search_screen)
        
    def show_simon_says(self):
        """@brief Cambia a la pantalla de simon says."""        
        self.stack.setCurrentWidget(self.simon_says_screen)
        
    def show_find_differences(self):
        """@brief Cambia a la pantalla de find differences."""        
        self.stack.setCurrentWidget(self.find_differences_screen)
        
    def show_browser(self):
        """@brief Cambia a la pantalla de browser."""        
        self.stack.setCurrentWidget(self.browser_screen)
         
    def show_settings(self):
        """@brief Cambia a la pantalla de settings."""        
        self.stack.setCurrentWidget(self.settings_screen)
        
        
        
    # =========================
    # PROACTIVE
    # =========================
    
    def _show_proactive_slot(self, suggestion: dict): 
        """
        @brief Slot para mostrar una pantalla proactiva dinámicamente.
        @param suggestion Diccionario con la información y acción de la sugerencia.
        """
        
        logger.info(f"[MAIN WINDOW] Mostrando sugerencia proactiva {suggestion['title']}")
        
        # ProactiveScreen
        self.proactive_screen = ProactiveScreen(
            suggestion=suggestion,
            controller=self.controller,
            on_accept=self._on_proactive_accept,
            on_dismiss=self._on_proactive_dismiss,
        )
        
        self.stack.addWidget(self.proactive_screen)
        self.stack.setCurrentWidget(self.proactive_screen)
        
        
    def _on_proactive_accept(self, action: dict):
        """@brief Callback para manejar la aceptación de una sugerencia proactiva."""
        self._remove_proactive_screen()
        ACTION_MAP = {
            "word_search": self.show_games,
            "memory": self.show_games,
            "mobility": self.show_launcher,

        }
        
        ACTION_MAP.get(action, self.show_launcher)()
        
        
    def _on_proactive_dismiss(self): 
        """@brief Callback para manejar el rechazo de una sugerencia proactiva."""
        self._remove_proactive_screen()
        self.show_launcher()
    
    
    def _remove_proactive_screen(self): 
        """@brief Limpia y libera memoria de la pantalla proactiva dinámica."""        
        if hasattr(self, "proactive_screen") and self.proactive_screen:
            self.stack.removeWidget(self.proactive_screen)
            self.proactive_screen.deleteLater()
            self.proactive_screen = None
