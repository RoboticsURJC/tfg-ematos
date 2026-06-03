import logging
import requests


class RemoteHandler(logging.Handler):

    def __init__(self, url):
        super().__init__()
        self.url = url

    def emit(self, record):
        try:
            msg = self.format(record)

            requests.post(
                self.url,
                json={"text": msg},
                timeout=1
            )

        except Exception as e:
            print("[REMOTE LOG ERROR]", e)
