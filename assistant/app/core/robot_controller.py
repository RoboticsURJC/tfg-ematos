"""
@file robot_controller.py
@brief Controlador principal del robot: orquesta todos los subsistemas.

Gestiona el ciclo de vida completo:
- Arranque y apagado
- Login / logout de usuarios
- Apertura y cierre de apps
- Conexión con la interfaz gráfica (UI)
"""

import os
import json

from app.core.logger import logger
from app.core.app_registry import AppRegistry
from app.core.assistant_engine import AssistantEngine
from app.core.session_manager import SessionManager
from app.core.state_machine import StateMachine
from app.ui.display import FaceDisplay
from app.ui.state import UIState
from app.core.system_apps import SystemApps
from app.core.game_router import GameRouter
from app.ui.apps.calendar.calendar_store import CalendarStore
from app.ui.apps.reminder.reminder_store import ReminderStore
from app.ui.apps.reminder.reminder_scheduler import ReminderScheduler
from app.ui.apps.proactive.proactive_scheduler import ProactiveScheduler


class RobotController:
    """
    @brief Controlador central del sistema robótico.

    Coordina: AssistantEngine, FaceDisplay, SessionManager,
    StateMachine, AppRegistry y la UI gráfica (opcional).
    """

    def __init__(self):
        """
        @brief Inicializa todos los subsistemas del robot.

        Lee la configuración desde config/config.json y construye
        el AssistantEngine con la URL del servidor LLM y la ruta
        al modelo Vosk.
        """
        self.ui = None

        # Subsistemas core
        self.state_machine = StateMachine()
        self.session = SessionManager()
        self.registry = AppRegistry()
        self.registry.register_defaults()
        self.calendar_store = CalendarStore()
        self.reminder_store = ReminderStore()
        self.game_router = None
     
        # UI compartida
        self.ui_state = UIState()
        self.display = FaceDisplay()
        self.display.start()

        # Cargar configuración
        base = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base, "..", "config", "config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        voice_cfg  = config.get("voice", {})
        server_cfg = config.get("server", {})

        llm_base = server_cfg.get("llm_url", "").rstrip("/")
        server_url = llm_base

        # Modelo y timeout desde config
        llm_model   = server_cfg.get("model", "groq")
        llm_timeout = server_cfg.get("timeout", 90)

        # Nombre clave del micrófono (clave correcta del config)
        mic_name = voice_cfg.get("mic_name_keyword", "AB13X")

        logger.info(f"[CONTROLLER] LLM URL: {server_url} | modelo: {llm_model}")
        logger.info(f"[CONTROLLER] micrófono buscado: '{mic_name}'")

        # Motor del asistente
        self.assistant = AssistantEngine(
            ui_state=self.ui_state,
            display=self.display,
            calendar_store=self.calendar_store,
            reminder_store=self.reminder_store,
            model_path=voice_cfg.get("vosk_model_path"),
            server_url=server_url,
            mic_name=mic_name,
            llm_model=llm_model,
            llm_timeout=llm_timeout
        )
        
        
        self.reminder_scheduler = ReminderScheduler(
            self.reminder_store,
            self.assistant.tts,
            self.display        
        )
        
        self.proactive_scheduler = ProactiveScheduler(
            tts=self.assistant.tts,
            display=self.display,
            on_suggest=self._on_proactive_suggest,
            memory_interval=45 * 60,
            mobility_interval=30 * 60,
            start_delay=10 * 60        
        )
        
        logger.info("[CONTROLLER] controlador listo")



    # =========================================================
    # FUNCIONAMIENTO DE PROACTIVE
    # =========================================================
    def _on_proactive_suggest(self, suggestion: dict):
        """
        Callback llamado por Proactive
        """
        if not self.ui:
            logger.warning("[CONTROLLER] Sugerencia proactiva")
            return
        
        try:
            self.ui.show_proactive_signal.emit(suggestion)
        
        except Exception as e:
            logger.error("[CONTROLLER] Error emitido de proactividad")

    # =========================================================
    # CONEXIÓN CON LA UI
    # =========================================================

    def set_ui(self, ui):
        """
        @brief Registra la referencia a la interfaz gráfica.
        @param ui  Objeto de la UI principal.
        """
        self.ui = ui
        self.game_router = GameRouter(self)

    # =========================================================
    # ARRANQUE
    # =========================================================

    def start(self):
        """
        @brief Arranca el sistema (boot sequence)."""
        logger.info("[CONTROLLER] Iniciando RobotController")
        self.boot()
        if self.ui:
            self.ui.show_boot()

    def boot(self):
        """@brief Establece el estado de arranque inicial."""
        self.state_machine.set_state(StateMachine.BOOT)
        self.display.set_estado("Iniciando sistema")
        logger.info("[CONTROLLER] boot")

    # =========================================================
    # LOGIN / LOGOUT
    # =========================================================

    def login(self, username):
        """
        @brief Inicia sesión de un usuario y arranca el asistente.

        Actualiza sesión, estado visual, memoria del asistente y
        lanza el bucle de escucha STT.

        @param username  Nombre del usuario que inicia sesión.
        """
        self.session.login(username)
        self.ui_state.set_user(username)
        self.state_machine.set_state(StateMachine.HOME)
        self.display.set_estado(f"Hola {username}")

        # Saludo personalizado + arranque de escucha
        self.assistant.set_user(username)
        self.assistant.start()

        if self.ui:
            self.ui.launcher_screen.set_user(username)
            self.ui.show_launcher()

        logger.info(f"[CONTROLLER]] login: {username}")
        
        self.reminder_scheduler.start()
        logger.info(f"[CONTROLLER] Scheduler reminder iniciado para usuario {username}")

        self.proactive_scheduler.start()
        logger.info(f"[CONTROLLER] Scheduler proactive iniciado para usuario {username}")


    def logout(self):
        """
        @brief Cierra la sesión activa y detiene el asistente."""
        username = self.session.current_user
        self.session.logout()
        self.ui_state.reset()
        self.display.set_estado("Sesión cerrada")
        self.assistant.stop()
        logger.info(f"[CONTROLLER]] logout: {username}")
        self.proactive_scheduler.stop()
        if self.ui:
            self.ui.show_login()

    # =========================================================
    # APPS
    # =========================================================
    
    def open_game(self, game_id):
        if not self.game_router:
            logger.error("[CONTROLLER]  GameRouter no inicializado")
            return
            
        self.game_router.open_game(game_id)
    
    def open_app(self, app_name):
        """
        @brief Abre una aplicación del launcher.
        @param app_name  Nombre de la app a abrir.
        """
        result = SystemApps.launch(app_name)
        
        if isinstance(result, str) and result.startswith("internal"):
            
            app = result.split(":")[1]
            
            if app == "notes":
                self.ui.show_notes()
                
            if app == "calendar":
                self.ui.show_calendar()
                
            if app == "reminder":
                self.ui.show_reminder()
                
            if app == "games":
                self.ui.show_games()
                return
            
            return
            
        # ~ APPS externas
        self.ui_state.open_app(app_name)
        self.state_machine.set_state(StateMachine.APP)
        self.display.set_estado(f"App: {app_name}")
        
        SystemApps.launch(app_name)
        
        logger.info(f"[CONTROLLER]] app abierta: {app_name}")
        
        

    def close_app(self):
        """@brief Cierra la app activa y vuelve al launcher."""
        self.ui_state.close_app()
        self.state_machine.set_state(StateMachine.HOME)
        if self.ui:
            self.ui.show_launcher()
        logger.info("[CONTROLLER]] app cerrada")

    # =========================================================
    # APAGADO
    # =========================================================

    def shutdown(self):
        """
        @brief Apaga el sistema de forma ordenada.

        Detiene el asistente, la pantalla y la UI.
        """
        logger.info("[CONTROLLER]] apagando sistema")
        self.state_machine.set_state(StateMachine.SHUTDOWN)
        self.assistant.stop()
        self.display.set_estado("Apagando...")
        # ~ self.display.stop()
        if self.ui:
            self.ui.close()
        
        if hasattr(self, "proactive_scheduler"):
            self.proactive_scheduler.stop()
        
        if hasattr(self, "tts"):
            self.tts.stop()
        
