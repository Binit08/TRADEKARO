"""Event Bus for decoupled communication."""
import logging
import threading
import queue
from typing import Dict, List, Callable, Type, Any

logger = logging.getLogger(__name__)


class EventBus:
    """Thread-safe Pub/Sub Event Bus."""
    
    def __init__(self):
        self._subscribers: Dict[Type, List[Callable[[Any], None]]] = {}
        self._queue = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None
        
    def subscribe(self, event_type: Type, callback: Callable[[Any], None]) -> None:
        """Register a callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        
    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers asynchronously."""
        self._queue.put(event)
        
    def start(self) -> None:
        """Start the event dispatch loop in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._dispatch_loop, daemon=True, name="EventBus")
        self._thread.start()
        logger.info("EventBus started.")
        
    def stop(self) -> None:
        """Stop the event dispatch loop gracefully."""
        self._running = False
        self._queue.put(None)  # Sentinel value to unblock queue.get()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("EventBus stopped.")
        
    def _dispatch_loop(self) -> None:
        """Consume events from the queue and route to subscribers."""
        while self._running:
            try:
                event = self._queue.get(timeout=1.0)
                if event is None:
                    continue  # Sentinel value or empty
                    
                event_type = type(event)
                subscribers = self._subscribers.get(event_type, [])
                
                for callback in subscribers:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"Error in EventBus subscriber {callback} for event {event_type}: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"EventBus critical error: {e}")
