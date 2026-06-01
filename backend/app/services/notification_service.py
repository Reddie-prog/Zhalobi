from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models import Notification


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, message: str,
                     complaint_id: Optional[int] = None,
                     notification_type: str = "info") -> Notification:
        notif = Notification(
            user_id=user_id,
            complaint_id=complaint_id,
            message=message,
            notification_type=notification_type,
        )
        self.db.add(notif)
        await self.db.commit()
        return notif

    async def get_user_notifications(self, user_id: int) -> List[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(30)
        )
        return result.scalars().all()

    async def mark_read(self, notification_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notif = result.scalar_one_or_none()
        if notif:
            notif.is_read = True
            await self.db.commit()
            return True
        return False

    async def mark_all_read(self, user_id: int):
        result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        for n in result.scalars().all():
            n.is_read = True
        await self.db.commit()

    async def unread_count(self, user_id: int) -> int:
        cnt = await self.db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return cnt or 0
