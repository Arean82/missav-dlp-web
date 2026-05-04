import queue
import json
import threading

class EventBus:
    def __init__(self):
        self.subscribers = []
        self._lock = threading.Lock()

    def subscribe(self):
        q = queue.Queue(maxsize=10)
        with self._lock:
            self.subscribers.append(q)
        return q

    def unsubscribe(self, q):
        with self._lock:
            if q in self.subscribers:
                self.subscribers.remove(q)

    def publish(self, event_type, data):
        message = json.dumps({"type": event_type, "data": data})
        with self._lock:
            subs = self.subscribers[:]
        
        for q in subs:
            try:
                q.put_nowait(message)
            except queue.Full:
                self.unsubscribe(q)

event_bus = EventBus()
