from datetime import datetime
from threading import Lock

_logs = {
    "llm": [],
    "recognition": [],
    "system": []
}

_lock = Lock()

MAX_LOGS = 300


def add_log(service: str, message: str):

    with _lock:

        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "text": message
        }

        if service not in _logs:
            _logs[service] = []

        _logs[service].append(entry)

        if len(_logs[service]) > MAX_LOGS:
            _logs[service] = _logs[service][-MAX_LOGS:]


def get_logs(service: str):

    with _lock:
        return _logs.get(service, [])


def clear_logs(service: str):

    with _lock:
        _logs[service] = []   


def get_all_logs():

    with _lock:
        return dict(_logs)