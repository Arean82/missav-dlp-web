# app_files/event_bus.py 
# Simple Event System for SSE

import queue
import json

class EventBus:
    def __init__(self):
        self.subscribers = []

    def subscribe(self):
        q = queue.Queue(maxsize=10)
        self.subscribers.append(q)
        return q

    def unsubscribe(self, q):
        if q in self.subscribers:
            self.subscribers.remove(q)

    def publish(self, event_type, data):
        message = json.dumps({"type": event_type, "data": data})
        for q in self.subscribers[:]: # Iterate over a copy to allow removal
            try:
                q.put_nowait(message)
            except queue.Full:
                self.unsubscribe(q)

event_bus = EventBus()
