"""
Observer pattern: async event bus for complaint lifecycle events.
Subscribers are registered at startup and notified concurrently when events occur.
"""
import asyncio
import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger(__name__)


class EventType:
    CREATED = "complaint.created"
    STATUS_CHANGED = "complaint.status_changed"
    ESCALATED = "complaint.escalated"
    ASSIGNED = "complaint.assigned"
    RESOLVED = "complaint.resolved"


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, handler: Callable) -> None:
        self._subscribers.setdefault(event, []).append(handler)
        logger.info(f"Observer registered: {handler.__name__} → {event}")

    async def publish(self, event: str, data: Any) -> None:
        handlers = self._subscribers.get(event, [])
        if not handlers:
            return
        tasks = [asyncio.create_task(self._safe_call(h, data)) for h in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(self, handler: Callable, data: Any) -> None:
        try:
            await handler(data)
        except Exception as e:
            logger.error(f"Event handler {handler.__name__} failed: {e}")


event_bus = EventBus()
