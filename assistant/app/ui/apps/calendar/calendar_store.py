import json
import os


class CalendarStore:

    def __init__(self):
        self.path = os.path.join(os.path.dirname(__file__), "events.json")
        self.events = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return []

        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.events, f, indent=4, ensure_ascii=False)

    def add_event(self, date, title):
        self.events.append({
            "date": date,
            "title": title
        })
        self.save()

    def get_events(self, date):
        return [e for e in self.events if e["date"] == date]

    def delete_event(self, index):
        if 0 <= index < len(self.events):
            del self.events[index]
            self.save()
            
