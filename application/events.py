import logging
from collections import defaultdict
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)

# TODO Add more events


class RefreshType(str, Enum):
    STUDENTS = "student_changed"
    MOVEMENTS = "movement_added"


class EventBus:
    def __init__(self):
        self._subscribers: dict[RefreshType, list[Callable]] = defaultdict(list)

    # --- Subscription Pattern for UI Updates ---
    def subscribe(self, event: RefreshType, callback: Callable):
        """Allows a UI component to subscribe to data changes."""
        self._subscribers[event].append(callback)

    def unsubscribe(self, event: RefreshType, callback: Callable):
        if callback in self._subscribers[event]:
            self._subscribers[event].remove(callback)

    def notify(self, event: RefreshType, **data) -> None:
        """Notifies all subscribed components that data has changed."""
        for callback in list(self._subscribers[event]):
            try:
                callback(**data)
            except Exception as e:
                logger.exception(f"Subscriber error: {e}")
