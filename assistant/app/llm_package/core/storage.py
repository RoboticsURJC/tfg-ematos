import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "..", "results", "results.jsonl")


def load_results():
    if not os.path.exists(FILE):
        return []

    results = []
    with open(FILE, "r", encoding="utf-8") as f:
        for line in f:
            results.append(json.loads(line))
    return results


def save_result(result):
    result["timestamp"] = datetime.now().isoformat()

    os.makedirs(os.path.dirname(FILE), exist_ok=True)

    with open(FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")