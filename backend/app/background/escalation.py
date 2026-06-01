"""
Async background task: checks every hour for overdue complaints and escalates them
automatically (no human interaction — asynchronous mode, no paper trail).
"""
import asyncio
import logging
from ..database import AsyncSessionLocal
from ..services.complaint_service import ComplaintService
from ..config import settings

logger = logging.getLogger(__name__)


async def run_escalation_check():
    logger.info("Escalation check starting...")
    try:
        async with AsyncSessionLocal() as db:
            svc = ComplaintService(db)
            overdue = await svc.get_overdue_complaints(hours=settings.escalation_hours)
            count = 0
            for complaint in overdue:
                try:
                    await svc.escalate_complaint(
                        complaint.id,
                        f"Автоматическая эскалация: заявка не обработана за "
                        f"{settings.escalation_hours} часов",
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to escalate #{complaint.id}: {e}")
            logger.info(f"Escalation check done — {count} complaints escalated")
    except Exception as e:
        logger.error(f"Escalation check error: {e}")


async def escalation_loop():
    """Runs in background every hour via asyncio task."""
    while True:
        await asyncio.sleep(3600)
        await run_escalation_check()
