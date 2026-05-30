import requests
import logging

class RemoteHandler(logging.Handler):

    def __init__(self, url, service_name):
        super().__init__()
        self.url = url
        self.service_name = service_name

    def emit(self, record):
        try:
            requests.post(
                f"{self.url}/log/{self.service_name}",
                json={
                    "level": record.levelname,
                    "message": self.format(record),
                },
                timeout=1
            )
        except:
            pass
