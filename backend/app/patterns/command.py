"""
Command pattern: each complaint action (submit, change status, escalate, assign)
is encapsulated as a command object supporting execute/undo.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class Command(ABC):
    @abstractmethod
    async def execute(self) -> Any:
        pass

    @abstractmethod
    async def undo(self) -> Any:
        pass


class CommandHistory:
    def __init__(self):
        self._history: list = []

    def push(self, cmd: Command):
        self._history.append(cmd)

    def pop(self) -> Optional[Command]:
        return self._history.pop() if self._history else None

    @property
    def count(self):
        return len(self._history)


class SubmitComplaintCommand(Command):
    def __init__(self, service, user_id: int, data: dict):
        self._service = service
        self._user_id = user_id
        self._data = data
        self._created_id: Optional[int] = None

    async def execute(self):
        result = await self._service.create_complaint(self._user_id, self._data)
        self._created_id = result.id
        logger.info(f"Command executed: SubmitComplaint → ticket={result.ticket_number}")
        return result

    async def undo(self):
        if self._created_id:
            await self._service.cancel_complaint(self._created_id)
            logger.info(f"Command undone: SubmitComplaint #{self._created_id}")


class ChangeStatusCommand(Command):
    def __init__(self, service, complaint_id: int, new_status: str,
                 admin_id: int, comment: str = ""):
        self._service = service
        self._complaint_id = complaint_id
        self._new_status = new_status
        self._admin_id = admin_id
        self._comment = comment
        self._old_status: Optional[str] = None

    async def execute(self):
        complaint = await self._service.get_complaint(self._complaint_id)
        if complaint:
            self._old_status = complaint.status
        result = await self._service.update_status(
            self._complaint_id, self._new_status, self._admin_id, self._comment
        )
        logger.info(f"Command executed: ChangeStatus #{self._complaint_id} → {self._new_status}")
        return result

    async def undo(self):
        if self._old_status:
            await self._service.update_status(
                self._complaint_id, self._old_status, self._admin_id, "Отмена изменения статуса"
            )
            logger.info(f"Command undone: ChangeStatus #{self._complaint_id} → {self._old_status}")


class EscalateComplaintCommand(Command):
    def __init__(self, service, complaint_id: int, reason: str = "Автоэскалация"):
        self._service = service
        self._complaint_id = complaint_id
        self._reason = reason

    async def execute(self):
        result = await self._service.escalate_complaint(self._complaint_id, self._reason)
        logger.info(f"Command executed: Escalate #{self._complaint_id}")
        return result

    async def undo(self):
        await self._service.update_status(
            self._complaint_id, "in_progress", None, "Эскалация отменена"
        )


class AssignComplaintCommand(Command):
    def __init__(self, service, complaint_id: int, assignee_id: Optional[int], admin_id: int):
        self._service = service
        self._complaint_id = complaint_id
        self._assignee_id = assignee_id
        self._admin_id = admin_id
        self._prev_assignee: Optional[int] = None

    async def execute(self):
        complaint = await self._service.get_complaint(self._complaint_id)
        if complaint:
            self._prev_assignee = complaint.assigned_to
        result = await self._service.assign_complaint(
            self._complaint_id, self._assignee_id, self._admin_id
        )
        logger.info(f"Command executed: Assign #{self._complaint_id} → user #{self._assignee_id}")
        return result

    async def undo(self):
        await self._service.assign_complaint(
            self._complaint_id, self._prev_assignee, self._admin_id
        )
