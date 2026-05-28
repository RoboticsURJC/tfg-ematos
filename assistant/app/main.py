import json
import os
import sys
import logging

from PyQt5.QtWidgets import QApplication, QShortcut
from PyQt5.QtGui import QKeySequence

from app.core.robot_controller import RobotController
from app.ui.main_window import MainWindow
from app.core.logger import logger


def main():

    logger.info("Iniciando sistema")

    app = QApplication(sys.argv)

    controller = RobotController()

    window = MainWindow(controller)
    controller.set_ui(window)

    # Atajo de teclado para salir
    exit_shortcut = QShortcut(QKeySequence("Esc"), window)
    exit_shortcut.activated.connect(app.quit)

    window.showFullScreen()

    controller.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
