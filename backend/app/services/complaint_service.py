import random
import string
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from ..models import Complaint, ComplaintEvent, Category, User
from ..patterns.observer import event_bus, EventType


def _gen_ticket() -> str:
    year = datetime.now().strftime("%y")
    rnd = "".join(random.choices(string.digits, k=6))
    return f"ЖКХ-{year}-{rnd}"


class ComplaintService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_complaint(self, user_id: int, data: dict) -> Complaint:
        ticket = _gen_ticket()
        while await self._ticket_exists(ticket):
            ticket = _gen_ticket()

        complaint = Complaint(
            ticket_number=ticket,
            user_id=user_id,
            category_id=data["category_id"],
            title=data["title"],
            description=data["description"],
            address=data["address"],
            priority=data.get("priority", "medium"),
            status="new",
        )
        self.db.add(complaint)
        await self.db.flush()

        self.db.add(ComplaintEvent(
            complaint_id=complaint.id,
            event_type="created",
            new_status="new",
            created_by=user_id,
            comment="Жалоба зарегистрирована",
        ))
        await self.db.commit()

        complaint = await self.get_complaint(complaint.id)
        await event_bus.publish(EventType.CREATED, {
            "complaint_id": complaint.id,
            "ticket_number": complaint.ticket_number,
            "user_id": user_id,
            "title": complaint.title,
        })
        return complaint

    async def get_complaint(self, complaint_id: int) -> Optional[Complaint]:
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.id == complaint_id)
            .options(
                selectinload(Complaint.user),
                selectinload(Complaint.category),
                selectinload(Complaint.events).selectinload(ComplaintEvent.creator),
                selectinload(Complaint.assigned_user),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_ticket(self, ticket: str) -> Optional[Complaint]:
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.ticket_number == ticket)
            .options(
                selectinload(Complaint.user),
                selectinload(Complaint.category),
                selectinload(Complaint.events).selectinload(ComplaintEvent.creator),
            )
        )
        return result.scalar_one_or_none()

    async def get_user_complaints(self, user_id: int, skip: int = 0, limit: int = 50):
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.user_id == user_id)
            .options(
                selectinload(Complaint.user),
                selectinload(Complaint.category),
            )
            .order_by(Complaint.created_at.desc())
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_all_complaints(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
    ):
        query = (
            select(Complaint)
            .options(
                selectinload(Complaint.user),
                selectinload(Complaint.category),
            )
            .order_by(Complaint.created_at.desc())
        )
        if status:
            query = query.where(Complaint.status == status)
        if category_id:
            query = query.where(Complaint.category_id == category_id)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def update_status(
        self, complaint_id: int, new_status: str,
        admin_id: Optional[int], comment: str = ""
    ) -> Optional[Complaint]:
        complaint = await self.get_complaint(complaint_id)
        if not complaint:
            return None
        old_status = complaint.status
        complaint.status = new_status
        complaint.updated_at = datetime.utcnow()
        if new_status == "resolved":
            complaint.resolved_at = datetime.utcnow()

        self.db.add(ComplaintEvent(
            complaint_id=complaint_id,
            event_type="status_changed",
            old_status=old_status,
            new_status=new_status,
            comment=comment,
            created_by=admin_id,
        ))
        await self.db.commit()

        await event_bus.publish(EventType.STATUS_CHANGED, {
            "complaint_id": complaint_id,
            "ticket_number": complaint.ticket_number,
            "user_id": complaint.user_id,
            "old_status": old_status,
            "new_status": new_status,
        })
        return await self.get_complaint(complaint_id)

    async def escalate_complaint(self, complaint_id: int, reason: str) -> Optional[Complaint]:
        complaint = await self.get_complaint(complaint_id)
        if not complaint:
            return None
        old_status = complaint.status
        complaint.status = "escalated"
        complaint.escalated_at = datetime.utcnow()
        complaint.priority = "critical"
        complaint.updated_at = datetime.utcnow()

        self.db.add(ComplaintEvent(
            complaint_id=complaint_id,
            event_type="escalated",
            old_status=old_status,
            new_status="escalated",
            comment=reason,
        ))
        await self.db.commit()

        await event_bus.publish(EventType.ESCALATED, {
            "complaint_id": complaint_id,
            "ticket_number": complaint.ticket_number,
            "user_id": complaint.user_id,
            "reason": reason,
        })
        return await self.get_complaint(complaint_id)

    async def assign_complaint(
        self, complaint_id: int, assignee_id: Optional[int], admin_id: int
    ) -> Optional[Complaint]:
        complaint = await self.get_complaint(complaint_id)
        if not complaint:
            return None
        complaint.assigned_to = assignee_id
        if complaint.status == "new":
            complaint.status = "in_progress"
        complaint.updated_at = datetime.utcnow()

        self.db.add(ComplaintEvent(
            complaint_id=complaint_id,
            event_type="assigned",
            comment=f"Назначено исполнителю #{assignee_id}",
            created_by=admin_id,
        ))
        await self.db.commit()

        await event_bus.publish(EventType.ASSIGNED, {
            "complaint_id": complaint_id,
            "assignee_id": assignee_id,
        })
        return await self.get_complaint(complaint_id)

    async def cancel_complaint(self, complaint_id: int):
        complaint = await self.get_complaint(complaint_id)
        if complaint:
            await self.db.delete(complaint)
            await self.db.commit()

    async def get_overdue_complaints(self, hours: int = 72) -> List[Complaint]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.db.execute(
            select(Complaint).where(
                and_(
                    Complaint.status.in_(["new", "in_progress"]),
                    Complaint.created_at <= cutoff,
                    Complaint.escalated_at.is_(None),
                )
            )
        )
        return result.scalars().all()

    async def get_stats(self) -> dict:
        total = await self.db.scalar(select(func.count(Complaint.id))) or 0
        new_c = await self.db.scalar(
            select(func.count(Complaint.id)).where(Complaint.status == "new")
        ) or 0
        in_prog = await self.db.scalar(
            select(func.count(Complaint.id)).where(Complaint.status == "in_progress")
        ) or 0
        escalated = await self.db.scalar(
            select(func.count(Complaint.id)).where(Complaint.status == "escalated")
        ) or 0
        resolved = await self.db.scalar(
            select(func.count(Complaint.id)).where(Complaint.status == "resolved")
        ) or 0
        closed = await self.db.scalar(
            select(func.count(Complaint.id)).where(Complaint.status == "closed")
        ) or 0
        auto_processed = await self.db.scalar(
            select(func.count(ComplaintEvent.id)).where(
                and_(
                    ComplaintEvent.event_type == "escalated",
                    ComplaintEvent.created_by.is_(None),
                )
            )
        ) or 0
        rate = round((resolved + closed) / total * 100, 1) if total > 0 else 0.0

        return {
            "total_complaints": total,
            "new_complaints": new_c,
            "in_progress_complaints": in_prog,
            "escalated_complaints": escalated,
            "resolved_complaints": resolved,
            "closed_complaints": closed,
            "auto_processed_count": auto_processed,
            "resolution_rate": rate,
        }

    async def _ticket_exists(self, ticket: str) -> bool:
        cnt = await self.db.scalar(
            select(func.count(Complaint.id)).where(Complaint.ticket_number == ticket)
        )
        return (cnt or 0) > 0
