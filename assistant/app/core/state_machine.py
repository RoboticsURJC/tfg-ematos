# app/core/state_machine.py

class StateMachine:
    """
    Máquina de estados global.
    """

    BOOT = "boot"

    LOGIN = "login"

    HOME = "home"

    ASSISTANT = "assistant"

    APP = "app"

    SETTINGS = "settings"

    ERROR = "error"

    SHUTDOWN = "shutdown"

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self):

        self.current_state = self.BOOT

    # =========================================================
    # SET
    # =========================================================

    def set_state(self, state):

        print(
            f"[STATE] {self.current_state} -> {state}"
        )

        self.current_state = state

    # =========================================================
    # GET
    # =========================================================

    def get_state(self):

        return self.current_state

    # =========================================================
    # CHECK
    # =========================================================

    def is_state(self, state):

        return self.current_state == state
