import requests
import logging

class RemoteHandler(logging.Handler):

    def __init__(self, url):
        super().__init__()
        self.url = url

    def emit(self, record):
        try:
            requests.post(
                f"{self.url}/log",
                json={
                    "level": record.levelname,
                    "message": self.format(record),
                }, 
                timeout=1
            )

        except:
            pass
