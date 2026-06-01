"""
Facade pattern: single entry point for all complaint operations.
Hides the complexity of services, commands, and event publishing from the API layer.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .command import (
    SubmitComplaintCommand, ChangeStatusCommand,
    EscalateComplaintCommand, AssignComplaintCommand, CommandHistory,
)
from ..services.complaint_service import ComplaintService
from ..services.notification_service import NotificationService


class ComplaintFacade:
    def __init__(self, db: AsyncSession):
        self._complaints = ComplaintService(db)
        self._notifications = NotificationService(db)
        self._history = CommandHistory()

    async def submit_complaint(self, user_id: int, data: dict):
        cmd = SubmitComplaintCommand(self._complaints, user_id, data)
        result = await cmd.execute()
        self._history.push(cmd)
        return result

    async def get_complaint(self, complaint_id: int):
        return await self._complaints.get_complaint(complaint_id)

    async def get_complaint_by_ticket(self, ticket: str):
        return await self._complaints.get_by_ticket(ticket)

    async def get_user_complaints(self, user_id: int, skip: int = 0, limit: int = 50):
        return await self._complaints.get_user_complaints(user_id, skip, limit)

    async def get_all_complaints(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
    ):
        return await self._complaints.get_all_complaints(skip, limit, status, category_id)

    async def change_status(self, complaint_id: int, new_status: str,
                            admin_id: int, comment: str = ""):
        cmd = ChangeStatusCommand(self._complaints, complaint_id, new_status, admin_id, comment)
        result = await cmd.execute()
        self._history.push(cmd)
        return result

    async def escalate(self, complaint_id: int, reason: str = "Автоэскалация"):
        cmd = EscalateComplaintCommand(self._complaints, complaint_id, reason)
        result = await cmd.execute()
        self._history.push(cmd)
        return result

    async def assign(self, complaint_id: int, assignee_id: Optional[int], admin_id: int):
        cmd = AssignComplaintCommand(self._complaints, complaint_id, assignee_id, admin_id)
        result = await cmd.execute()
        self._history.push(cmd)
        return result

    async def get_notifications(self, user_id: int):
        return await self._notifications.get_user_notifications(user_id)

    async def mark_notification_read(self, notification_id: int, user_id: int):
        return await self._notifications.mark_read(notification_id, user_id)

    async def mark_all_notifications_read(self, user_id: int):
        return await self._notifications.mark_all_read(user_id)

    async def get_stats(self):
        return await self._complaints.get_stats()

    async def undo_last(self):
        cmd = self._history.pop()
        if cmd:
            await cmd.undo()
            return True
        return False
