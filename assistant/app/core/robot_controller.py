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

        logger.info(f"[ROBOT] LLM URL: {server_url} | modelo: {llm_model}")
        logger.info(f"[ROBOT] micrófono buscado: '{mic_name}'")

        # Motor del asistente
        self.assistant = AssistantEngine(
            ui_state=self.ui_state,
            display=self.display,
            model_path=voice_cfg.get("vosk_model_path"),
            server_url=server_url,
            mic_name=mic_name,
            llm_model=llm_model,
            llm_timeout=llm_timeout
        )

        logger.info("[ROBOT] controlador listo")

    # =========================================================
    # CONEXIÓN CON LA UI
    # =========================================================

    def set_ui(self, ui):
        """
        @brief Registra la referencia a la interfaz gráfica.
        @param ui  Objeto de la UI principal.
        """
        self.ui = ui

    # =========================================================
    # ARRANQUE
    # =========================================================

    def start(self):
        """
        @brief Arranca el sistema (boot sequence)."""
        logger.info("---------- Iniciando RobotController ----------")
        self.boot()
        if self.ui:
            self.ui.show_boot()

    def boot(self):
        """@brief Establece el estado de arranque inicial."""
        self.state_machine.set_state(StateMachine.BOOT)
        self.display.set_estado("Iniciando sistema")
        logger.info("[ROBOT] boot")

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

        logger.info(f"[ROBOT] login: {username}")

    def logout(self):
        """
        @brief Cierra la sesión activa y detiene el asistente."""
        username = self.session.current_user
        self.session.logout()
        self.ui_state.reset()
        self.display.set_estado("Sesión cerrada")
        self.assistant.stop()
        logger.info(f"[ROBOT] logout: {username}")
        if self.ui:
            self.ui.show_login()

    # =========================================================
    # APPS
    # =========================================================

    def open_app(self, app_name):
        """
        @brief Abre una aplicación del launcher.
        @param app_name  Nombre de la app a abrir.
        """
        self.ui_state.open_app(app_name)
        self.state_machine.set_state(StateMachine.APP)
        self.display.set_estado(f"App: {app_name}")
        logger.info(f"[ROBOT] app abierta: {app_name}")

    def close_app(self):
        """@brief Cierra la app activa y vuelve al launcher."""
        self.ui_state.close_app()
        self.state_machine.set_state(StateMachine.HOME)
        if self.ui:
            self.ui.show_launcher()
        logger.info("[ROBOT] app cerrada")

    # =========================================================
    # APAGADO
    # =========================================================

    def shutdown(self):
        """
        @brief Apaga el sistema de forma ordenada.

        Detiene el asistente, la pantalla y la UI.
        """
        logger.info("[ROBOT] apagando sistema")
        self.state_machine.set_state(StateMachine.SHUTDOWN)
        self.assistant.stop()
        self.display.set_estado("Apagando...")
        self.display.stop()
        if self.ui:
            self.ui.close()
