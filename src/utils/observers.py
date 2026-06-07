from dataclasses import dataclass
from typing import Callable, Dict, List, Type


@dataclass
class BaseEvent:
    pass


@dataclass
class UserRegisteredEvent(BaseEvent):
    user_id: int
    email: str


@dataclass
class UserBlockedEvent(BaseEvent):
    user_id: int


@dataclass
class StudentEnrolledEvent(BaseEvent):
    user_id: int
    course_id: int


@dataclass
class CourseCompletedEvent(BaseEvent):
    user_id: int
    course_id: int


@dataclass
class QuizPassedEvent(BaseEvent):
    user_id: int
    quiz_id: int
    score_percent: float


class EventBus:
    """Observer pattern: publish/subscribe event bus."""

    def __init__(self):
        self._listeners: Dict[Type[BaseEvent], List[Callable]] = {}
        self._history: List[BaseEvent] = []

    def subscribe(self, event_type: Type[BaseEvent], handler: Callable) -> None:
        self._listeners.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: Type[BaseEvent], handler: Callable) -> None:
        if event_type in self._listeners:
            self._listeners[event_type] = [
                h for h in self._listeners[event_type] if h != handler
            ]

    def publish(self, event: BaseEvent) -> None:
        self._history.append(event)
        for handler in self._listeners.get(type(event), []):
            handler(event)

    def get_history(self) -> List[BaseEvent]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
