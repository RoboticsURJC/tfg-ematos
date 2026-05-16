import sys
import logging

from PyQt5.QtWidgets import QApplication

from app.ui.face_client import FaceClient
from app.ui.theme import MAIN_STYLE
from app.core.assistant_engine import AssistantEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


def main():

    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    app.setStyleSheet(MAIN_STYLE)

    engine = None

    def on_user(user):
        engine.on_user(user)

    client = FaceClient(on_user)

    engine = AssistantEngine(client.display)

    client.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()