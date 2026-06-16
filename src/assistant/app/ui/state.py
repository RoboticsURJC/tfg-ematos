# app/ui/state.py

"""
@file ui_state.py
@brief Centralización del estado global de la interfaz de usuario.
@details Clase gestora de estado basada en el patrón Observer, permitiendo que
cualquier componente de la UI reaccione ante cambios en el usuario, aplicaciones,
modo del asistente o errores del sistema mediante señales Qt.
"""


from PyQt5.QtCore import QObject, pyqtSignal


class UIState(QObject):
    """
    @brief Gestión del estado global de la aplicación.
    @details Centraliza todas las variables de estado críticas y ofrece señales 
    para notificar cambios en tiempo real a los widgets interesados.
    
    @attr user_changed Señal al cambiar el usuario activo.
    @attr screen_changed Señal al navegar entre pantallas.
    @attr app_changed Señal al abrir/cerrar una aplicación.
    @attr status_changed Señal al actualizar el mensaje de estado del sistema.
    @attr listening_changed Señal al cambiar el estado de detección de voz.
    @attr speaking_changed Señal al cambiar el estado de síntesis de voz.
    @attr loading_changed Señal de cambio en el estado de carga (busy indicator).
    @attr error_occurred Señal de notificación de errores globales.
    @attr theme_changed Señal al cambiar el tema visual (dark/light).
    """

   
    user_changed = pyqtSignal(str)
    screen_changed = pyqtSignal(str)
    app_changed = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    listening_changed = pyqtSignal(bool)
    speaking_changed = pyqtSignal(bool)
    loading_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    theme_changed = pyqtSignal(str)

    
    def __init__(self):
        
        """@brief Inicializa el estado por defecto del sistema."""
        
        super().__init__()

        # =====================================================
        # USER
        # =====================================================

        self.current_user = None

        # =====================================================
        # UI
        # =====================================================

        self.current_screen = "boot"

        self.current_app = None

        self.current_theme = "dark"

        # =====================================================
        # ROBOT
        # =====================================================

        self.is_listening = False

        self.is_speaking = False

        self.is_loading = False

        # =====================================================
        # STATUS
        # =====================================================

        self.status_message = "Sistema iniciado"

        self.last_error = None

    # =========================================================
    # USER
    # =========================================================

    def set_user(self, user: str):
        """
        @brief Define el usuario actual y emite notificación.
        @param user Nombre del usuario.
        """

        self.current_user = user
        self.user_changed.emit(user)

    def clear_user(self):
        """
        @brief Limpia el usuario actual y notifica a la UI que no hay sesión activa.
        """

        self.current_user = None
        self.user_changed.emit("")

    # =========================================================
    # SCREEN
    # =========================================================

    def set_screen(self, screen: str):
        """
        @brief Actualiza la pantalla actual y notifica el cambio.
        @param screen Identificador de la nueva pantalla.
        """

        self.current_screen = screen
        self.screen_changed.emit(screen)

    # =========================================================
    # APPS
    # =========================================================

    def open_app(self, app_name: str):
        """
        @brief Registra la apertura de una aplicación y emite la señal de cambio.
        @param app_name Identificador de la aplicación que se ha abierto.
        """

        self.current_app = app_name
        self.app_changed.emit(app_name)

    def close_app(self):
        """
        @brief Cierra la aplicación actual en el estado y notifica la desvinculación.
        """

        self.current_app = None
        self.app_changed.emit("")

    # =========================================================
    # STATUS
    # =========================================================

    def set_status(self, message: str):
        """
        @brief Actualiza el mensaje de estado mostrado al usuario.
        @param message Cadena de texto descriptiva.
        """

        self.status_message = message
        self.status_changed.emit(message)

    # =========================================================
    # LISTENING
    # =========================================================

    def set_listening(self, value: bool):
        """
        @brief Actualiza el estado de escucha del asistente y emite la señal.
        @param value True si el asistente está escuchando, False en caso contrario.
        """

        self.is_listening = value
        self.listening_changed.emit(value)

    # =========================================================
    # SPEAKING
    # =========================================================

    def set_speaking(self, value: bool):
        """
        @brief Actualiza el estado de habla del asistente y emite la señal.
        @param value True si el asistente está hablando, False en caso contrario.
        """

        self.is_speaking = value
        self.speaking_changed.emit(value)

    # =========================================================
    # LOADING
    # =========================================================

    def set_loading(self, value: bool):
        """
        @brief Alterna el estado de carga visual (spinner/busy) en la UI.
        @param value True para activar indicador de carga, False para desactivarlo.
        """

        self.is_loading = value
        self.loading_changed.emit(value)

    # =========================================================
    # ERRORS
    # =========================================================

    def set_error(self, error_message: str):
        """
        @brief Almacena un mensaje de error y notifica a los suscriptores.
        @param error_message Descripción del error ocurrido.
        """

        self.last_error = error_message
        self.error_occurred.emit(error_message)

    def clear_error(self):
        """
        @brief Limpia el registro del último error almacenado en el estado.
        """

        self.last_error = None

    # =========================================================
    # THEMES
    # =========================================================

    def set_theme(self, theme_name: str):
        """
        @brief Cambia el tema visual de la aplicación y notifica la actualización.
        @param theme_name Nombre del tema (ej: 'dark', 'light').
        """

        self.current_theme = theme_name
        self.theme_changed.emit(theme_name)

    # =========================================================
    # RESET UI
    # =========================================================

    def reset(self):
        """
        @brief Restablece el estado global a sus valores de fábrica.
        @details Utilizado típicamente para cerrar sesiones y limpiar la UI.
        """

        self.current_user = None
        self.current_screen = "login"
        self.current_app = None
        self.is_listening = False
        self.is_speaking = False
        self.is_loading = False
        self.status_message = "Esperando usuario"
        self.last_error = None

        # signals

        self.user_changed.emit("")
        self.screen_changed.emit("login")
        self.app_changed.emit("")
        self.status_changed.emit(
            self.status_message
        )

        self.listening_changed.emit(False)
        self.speaking_changed.emit(False)
        self.loading_changed.emit(False)

    # =========================================================
    # DEBUG
    # =========================================================

    def dump_state(self):
        """
        @brief Retorna un snapshot del estado actual para propósitos de log/debug.
        @return Diccionario con el estado completo del sistema.
        """

        return {
            "user": self.current_user,
            "screen": self.current_screen,
            "app": self.current_app,
            "listening": self.is_listening,
            "speaking": self.is_speaking,
            "loading": self.is_loading,
            "status": self.status_message,
            "theme": self.current_theme,
            "error": self.last_error
        }
