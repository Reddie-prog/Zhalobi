from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import Notification, User
from ..schemas import NotificationResponse
from ..auth import get_current_user
from ..services.complaint_service import ComplaintService
from ..services.notification_service import NotificationService

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await ComplaintService(db).get_stats()


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await NotificationService(db).get_user_notifications(user.id)
    return [NotificationResponse.model_validate(n) for n in items]


@router.post("/notifications/{notification_id}/read")
async def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NotificationService(db).mark_read(notification_id, user.id)
    return {"ok": True}


@router.post("/notifications/read-all")
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NotificationService(db).mark_all_read(user.id)
    return {"ok": True}
