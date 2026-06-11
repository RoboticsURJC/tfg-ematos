import json
import os
import sys
import logging

from PyQt5.QtWidgets import QApplication, QShortcut
from PyQt5.QtGui import QKeySequence

from app.core.robot_controller import RobotController

from app.ui.main_window import MainWindow
from app.core.logger import logger


def shutdown(controller, app):
   logger.info("[MAIN] ESC -> apagado robot correctamente")
   
   try:
       controller.shutdown()
   
   except Exception as e:
       logger.error(f"[MAIN] error en stop {e}")
   
   app.quit()

def main():

    logger.info("[MAIN] Iniciando sistema")

    app = QApplication(sys.argv)

    controller = RobotController()

    window = MainWindow(controller)
    controller.set_ui(window)

    # Atajo de teclado para salir
    exit_shortcut = QShortcut(QKeySequence("Esc"), window)
    # ~ exit_shortcut.activated.connect(app.quit)
    exit_shortcut.activated.connect(lambda: shutdown(controller, app))


    window.showFullScreen()

    controller.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
