from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from ..database import get_db
from ..models import User
from ..schemas import ComplaintResponse, ComplaintUpdate, UserResponse
from ..auth import get_current_admin
from ..patterns.facade import ComplaintFacade

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/complaints", response_model=List[ComplaintResponse])
async def list_complaints(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    facade = ComplaintFacade(db)
    items = await facade.get_all_complaints(skip, limit, status, category_id)
    return [ComplaintResponse.model_validate(c) for c in items]


@router.patch("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: int,
    data: ComplaintUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    facade = ComplaintFacade(db)
    complaint = None

    if data.status:
        complaint = await facade.change_status(
            complaint_id, data.status, admin.id, data.comment or ""
        )
    if data.assigned_to is not None:
        complaint = await facade.assign(complaint_id, data.assigned_to, admin.id)
    if complaint is None:
        complaint = await facade.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")

    return ComplaintResponse.model_validate(complaint)


@router.post("/complaints/{complaint_id}/escalate", response_model=ComplaintResponse)
async def escalate(
    complaint_id: int,
    reason: str = "Ручная эскалация администратором",
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    facade = ComplaintFacade(db)
    complaint = await facade.escalate(complaint_id, reason)
    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")
    return ComplaintResponse.model_validate(complaint)


@router.delete("/complaints/{complaint_id}", status_code=204)
async def delete_complaint(
    complaint_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from ..models import Complaint
    c = await db.get(Complaint, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")
    await db.delete(c)
    await db.commit()


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.get("/route")
async def get_route(
    lat: float,
    lng: float,
    statuses: str = "new,in_progress,escalated",
    category_id: Optional[int] = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from ..services.route_optimizer import RouteOptimizer
    facade = ComplaintFacade(db)
    all_complaints = await facade.get_all_complaints(skip=0, limit=500, category_id=category_id)
    status_list = [s.strip() for s in statuses.split(",")]

    points = [
        {
            "id": c.id,
            "ticket_number": c.ticket_number,
            "title": c.title,
            "address": c.address,
            "status": c.status,
            "lat": c.lat,
            "lng": c.lng,
            "category": c.category.name if c.category else "—",
        }
        for c in all_complaints
        if c.status in status_list and c.lat and c.lng
    ]

    optimizer = RouteOptimizer()
    route, total_km = optimizer.optimize(lat, lng, points)

    return {
        "start": {"lat": lat, "lng": lng},
        "route": route,
        "total_km": total_km,
        "count": len(route),
    }
