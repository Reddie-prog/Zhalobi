"""
Observer subscribers: each handler is registered with the event bus at startup
and called asynchronously whenever a complaint event is published.
"""
import logging
from ..patterns.observer import event_bus, EventType
from ..database import AsyncSessionLocal
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


async def on_complaint_created(data: dict):
    async with AsyncSessionLocal() as db:
        svc = NotificationService(db)
        await svc.create(
            user_id=data["user_id"],
            message=f"Жалоба #{data['ticket_number']} принята. Ожидайте ответа.",
            complaint_id=data["complaint_id"],
            notification_type="success",
        )


async def on_status_changed(data: dict):
    labels = {
        "in_progress": "взята в работу",
        "escalated": "эскалирована для срочного рассмотрения",
        "resolved": "отмечена как решённая",
        "closed": "закрыта",
    }
    label = labels.get(data["new_status"], f"обновила статус")
    ntype = "warning" if data["new_status"] == "escalated" else "info"

    async with AsyncSessionLocal() as db:
        svc = NotificationService(db)
        await svc.create(
            user_id=data["user_id"],
            message=f"Жалоба #{data['ticket_number']} {label}.",
            complaint_id=data["complaint_id"],
            notification_type=ntype,
        )


async def on_escalated(data: dict):
    async with AsyncSessionLocal() as db:
        svc = NotificationService(db)
        await svc.create(
            user_id=data["user_id"],
            message=f"Жалоба #{data['ticket_number']} эскалирована: {data['reason']}",
            complaint_id=data["complaint_id"],
            notification_type="warning",
        )


def setup_handlers():
    event_bus.subscribe(EventType.CREATED, on_complaint_created)
    event_bus.subscribe(EventType.STATUS_CHANGED, on_status_changed)
    event_bus.subscribe(EventType.ESCALATED, on_escalated)
    logger.info("All event handlers registered")
