import sys
import logging
from PyQt5.QtWidgets import QApplication

from app.ui.face_client import FaceClient
from app.core.assistant_engine import AssistantEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


def main():

    app = QApplication(sys.argv)

    engine = None

    def on_user_authenticated(user):

        logger.info(
            f"Usuario autenticado: {user}"
        )

        engine.on_user(user)

    client = FaceClient(
        on_user_authenticated
    )

    engine = AssistantEngine(
        client.display
    )

    client.show()

    logger.info("Sistema iniciado")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()