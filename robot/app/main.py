import sys
import logging
from PyQt5.QtWidgets import QApplication

from ui.face_client import FaceClient
from core.assistant_engine import AssistantEngine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


if __name__ == "__main__":

    app = QApplication(sys.argv)

    engine = AssistantEngine()

    def on_user_authenticated(user):
        engine.on_user(user)

    client = FaceClient(on_user_authenticated)
    client.show()

    logger.info("Sistema iniciado")

    sys.exit(app.exec_())