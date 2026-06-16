# app/core/state_machine.py

##
# @file state_machine.py
# @brief Máquina de estados finitos (FSM) para el control del flujo operativo del robot.
# @details Centraliza, gestiona y valida las transiciones lógicas del ciclo de vida 
# y comportamiento del robot, previniendo estados indeterminados.
#

class StateMachine:
    """
    @brief Clase encargada de gobernar la máquina de estados global del sistema.
    """

    ## Estado inicial de arranque, carga de archivos de configuración y chequeo de hardware.
    BOOT = "boot"

    ## Pantalla de inicio esperando reconocimiento facial o login explícito de usuario.
    LOGIN = "login"

    ## Estado base o Launcher principal (Home) una vez que el usuario ha iniciado sesión.
    HOME = "home"

    ## Estado activo de interacción conversacional (STT, LLM y síntesis de voz TTS funcionando).
    ASSISTANT = "assistant"

    ## Estado en el que una aplicación (nativa o proceso externo) se encuentra en primer plano.
    APP = "app"

    ## Panel de configuración del sistema o menús técnicos de calibración en pantalla.
    SETTINGS = "settings"

    ## Estado crítico de fallo o excepción descontrolada en algún subsistema core.
    ERROR = "error"

    ## Secuencia de apagado ordenado, cierre de bases de datos y liberación de periféricos.
    SHUTDOWN = "shutdown"

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self):
        """
        @brief Inicializa la máquina de estados posicionando al sistema en la fase de arranque.
        """
        ## Almacena de forma volátil el identificador del estado actual del robot.
        self.current_state = self.BOOT

    # =========================================================
    # SET
    # =========================================================

    def set_state(self, state):
        """
        @brief Modifica de forma activa el estado del sistema y traza el cambio en consola.
        
        @param state Cadena de texto que representa el nuevo estado objetivo (se recomienda usar las constantes de la clase).
        """
        print(
            f"[STATE] {self.current_state} -> {state}"
        )
        self.current_state = state

    # =========================================================
    # GET
    # =========================================================

    def get_state(self):
        """
        @brief Recupera el estado actual en el que se encuentra el autómata.
        
        @return str Identificador de texto del estado actual.
        """
        return self.current_state

    # =========================================================
    # CHECK
    # =========================================================

    def is_state(self, state):
        """
        @brief Realiza una evaluación booleana rápida para comprobar si el sistema coincide con un estado concreto.
        
        @param state Estado con el que se desea contrastar la situación actual.
        @return bool True si coincide el estado consultado, False en caso contrario.
        """
        return self.current_state == state