# robot_controller.py

"""
@file robot_controller.py
@brief Controlador principal del robot: orquesta todos los subsistemas del ecosistema.
@details Gestiona el ciclo de vida completo del dispositivo:
- Secuencia de arranque (boot) y apagado seguro (shutdown).
- Control de inicio (login) y cierre de sesión (logout) de perfiles de usuario.
- Apertura, enrutamiento y clausura de aplicaciones del sistema o de estimulación cognitiva.
- Conexión y sincronización de señales con la interfaz gráfica de usuario (UI).
"""

import os
import json

from app.core.logger import logger
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
from PyQt5.QtCore import QMetaObject, Qt

class RobotController:
    """
    @brief Controlador central y núcleo lógico del sistema robótico.
    @details Coordina de manera asíncrona y mediante hilos el AssistantEngine, el FaceDisplay, 
    el SessionManager, la StateMachine y la interfaz gráfica de ventanas de PyQt5.
    """

    def __init__(self):
        """
        @brief Inicializa todos los subsistemas fundamentales del hardware y software del robot.
        @details Resuelve de forma dinámica y absoluta la ruta hacia `config/config.json`, parsea 
        las variables de red para el servidor de inferencia LLM y levanta las rutinas de los 
        planificadores (schedulers) de alertas y sugerencias proactivas.
        """
        ## Referencia directa hacia la ventana o vista principal de la UI gráfica (PyQt5 MainWindow).
        self.ui = None

        # --- Subsistemas Core del Firmware ---
        ## Instancia de la máquina de estados finitos que rige el flujo operativo del robot.
        self.state_machine = StateMachine()
        
        ## Gestor encargado del control de perfiles y sesiones activas.
        self.session = SessionManager()
        
        ## Repositorio en memoria del calendario de citas y eventos médicos.
        self.calendar_store = CalendarStore()
        
        ## Repositorio de base de datos local para alertas y recordatorios de pastillas.
        self.reminder_store = ReminderStore()
        
        ## Enrutador lógico de pantallas para los minijuegos de estimulación cognitiva.
        self.game_router = None

        # --- Interfaz Compartida y Gráficos Faciales ---
        ## Objeto de datos reactivo que encapsula el estado actual de la interfaz de usuario.
        self.ui_state = UIState()
        
        ## Controlador encargado del renderizado de la cara animada en la matriz o pantalla secundaria.
        self.display = FaceDisplay()
        self.display.start()

        # Cargar configuración desde el fichero JSON local del sistema de archivos
        base = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base, "..", "config", "config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        voice_cfg  = config.get("voice", {})
        server_cfg = config.get("server", {})

        llm_base   = server_cfg.get("llm_url", "").rstrip("/")
        server_url = llm_base

        llm_model   = server_cfg.get("model", "groq")
        llm_timeout = server_cfg.get("timeout", 90)

        mic_name = voice_cfg.get("mic_name_keyword", "USB")

        logger.info(f"[CONTROLLER] LLM URL: {server_url} | modelo: {llm_model}")
        logger.info(f"[CONTROLLER] micrófono buscado: '{mic_name}'")

        # --- Motor del Asistente por Voz ---
        ## Motor conversacional central (integra el STT Vosk, TTS y lógica de reintentos LLM).
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

        ## Planificador en segundo plano que vigila y dispara las alarmas de medicación cronometradas.
        self.reminder_scheduler = ReminderScheduler(
            self.reminder_store,
            self.assistant.tts,
            self.display
        )

        ## Planificador de sugerencias proactivas autónomas (rutinas de ejercicios cognitivos y recordatorios físicos).
        self.proactive_scheduler = ProactiveScheduler(
            tts=self.assistant.tts,
            display=self.display,
            on_suggest=self._on_proactive_suggest,
            # Expresión lambda inyectada para interrogar al STT en tiempo real sin acoplar clases de forma dura
            get_stt_state=lambda: self.assistant.stt.awake,
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
        @brief Método callback interno invocado de forma automática por el ProactiveScheduler.
        @details Intercepta la aparición de una nueva sugerencia autonómica y la emite hacia 
        el hilo principal de PyQt5 mediante el sistema de señales seguro de Qt.
        
        @param suggestion Diccionario con la metadata de la sugerencia (título, tipo, descripción).
        """
        if not self.ui:
            logger.warning("[CONTROLLER] Sugerencia proactiva recibida pero no hay UI conectada")
            return

        try:
            self.ui.show_proactive_signal.emit(suggestion)
        except Exception as e:
            logger.error(f"[CONTROLLER] Error al emitir señal de proactividad: {e}")

    def on_proactive_dismissed(self):
        """
        @brief Comunica al planificador que la tarjeta o modal de sugerencia proactiva ha sido cerrada.
        @details Debe invocarse obligatoriamente desde el hilo de la UI cuando el usuario interactúe 
        con los botones de acción ('Aceptar' o 'Ahora no') para restaurar el display gráfico facial.
        """
        self.proactive_scheduler.on_suggestion_dismissed()

    # =========================================================
    # CONEXIÓN CON LA UI
    # =========================================================

    def set_ui(self, ui):
        """
        @brief Registra de forma bidireccional la referencia hacia la interfaz gráfica de ventanas.
        
        @param ui Objeto que representa la ventana gráfica principal unificada.
        """
        self.ui = ui
        self.game_router = GameRouter(self)
        
        ui.refresh_reminders_signal.connect(ui.reminder_screen.refresh)
        ui.refresh_calendar_signal.connect(ui.calendar_screen.refresh)
        
        def _refresh_reminders():
            ui.refresh_reminders_signal.emit()


        def _refresh_calendar():
            ui.refresh_calendar_signal.emit()


        self.assistant.on_reminder_created = _refresh_reminders
        self.assistant.on_calendar_created = _refresh_calendar

    # =========================================================
    # ARRANQUE
    # =========================================================

    def start(self):
        """
        @brief Dispara la secuencia de arranque inicial del robot (Boot sequence).
        """
        logger.info("[CONTROLLER] Iniciando RobotController")
        self.boot()
        if self.ui:
            self.ui.show_boot()

    def boot(self):
        """
        @brief Establece el estado de inicialización nativo del hardware.
        """
        self.state_machine.set_state(StateMachine.BOOT)
        self.display.set_estado("Iniciando sistema")
        logger.info("[CONTROLLER] boot")

    # =========================================================
    # LOGIN / LOGOUT
    # =========================================================

    def login(self, username):
        """
        @brief Autentica e inicia la sesión de un usuario y activa los demonios de voz y agenda.
        @details Sincroniza el nombre de usuario con el Launcher, arranca el hilo de escucha continua 
        del STT, inicializa el reloj del planificador de recordatorios y el de estimulación proactiva.
        
        @param username Nombre de pila o identificador del usuario que toma el control del dispositivo.
        """
        self.session.login(username)
        self.ui_state.set_user(username)
        self.state_machine.set_state(StateMachine.HOME)
        self.display.set_estado(f"Hola {username}")

        self.assistant.set_user(username)
        self.assistant.start()

        if self.ui:
            self.ui.launcher_screen.set_user(username)
            self.ui.show_launcher()

        logger.info(f"[CONTROLLER] login: {username}")

        self.reminder_scheduler.start()
        logger.info(f"[CONTROLLER] Scheduler reminder iniciado para usuario {username}")

        self.proactive_scheduler.start()
        logger.info(f"[CONTROLLER] Scheduler proactive iniciado para usuario {username}")

    def logout(self):
        """
        @brief Clausura la sesión activa y detiene de forma segura los hilos de control y audio.
        """
        username = self.session.current_user
        self.session.logout()
        self.ui_state.reset()
        self.display.set_estado("Sesión cerrada")
        self.assistant.stop()
        logger.info(f"[CONTROLLER] logout: {username}")
        
        self.proactive_scheduler.stop()
        if self.ui:
            self.ui.show_login()

    # =========================================================
    # APPS
    # =========================================================

    def open_game(self, game_id):
        """
        @brief Delega en el enrutador de juegos la apertura de una aplicación cognitiva.
        
        @param game_id Identificador textual de la pantalla de juego ('memory', 'simon_says', etc).
        """
        if not self.game_router:
            logger.error("[CONTROLLER] GameRouter no inicializado")
            return

        self.game_router.open_game(game_id)

    def open_app(self, app_name):
        """
        @brief Abre una aplicación del sistema, discriminando si es interna o externa.
        @details Evalúa la respuesta devuelta por el lanzador estático; si detecta el prefijo 
        'internal', conmuta de forma limpia los paneles de PyQt5 de la aplicación sin invocar subprocesos.
        
        @param app_name Nombre clave de la aplicación solicitada.
        """
        result = SystemApps.launch(app_name)

        if isinstance(result, str) and result.startswith("internal"):
            app = result.split(":")[1]

            if app == "notes":
                self.ui.show_notes()

            elif app == "calendar":
                self.ui.show_calendar()

            elif app == "reminder":
                self.ui.show_reminder()

            elif app == "games":
                self.ui.show_games()
                return
                
            elif app == "browser":
                self.ui.show_browser()
                return
                 
            elif app == "settings":
                self.ui.show_settings()
                return
                 
            return

        # Aplicaciones externas (Procesos pesados del S.O.)
        self.ui_state.open_app(app_name)
        self.state_machine.set_state(StateMachine.APP)
        self.display.set_estado(f"App: {app_name}")

        SystemApps.launch(app_name)
        logger.info(f"[CONTROLLER] app abierta: {app_name}")

    def close_app(self):
        """
        @brief Destruye u oculta la ventana de la aplicación activa y reconduce al usuario al Launcher principal.
        """
        self.ui_state.close_app()
        self.state_machine.set_state(StateMachine.HOME)
        if self.ui:
            self.ui.show_launcher()
        logger.info("[CONTROLLER] app cerrada")

    # =========================================================
    # APAGADO
    # =========================================================

    def shutdown(self):
        """
        @brief Apaga el sistema de forma ordenada y libera descriptores de audio y vídeo.
        @details Transiciona el estado a SHUTDOWN, apaga los bucles de escucha del motor de voz, 
        cancela los hilos de los schedulers y clausura de forma nativa la UI de PyQt5.
        """
        logger.info("[CONTROLLER] apagando sistema")
        self.state_machine.set_state(StateMachine.SHUTDOWN)
        self.assistant.stop()
        self.display.set_estado("Apagando...")
        
        if self.ui:
            self.ui.close()

        if hasattr(self, "proactive_scheduler"):
            self.proactive_scheduler.stop()

        if hasattr(self, "tts"):
            self.tts.stop()
