from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import User, Category
from ..schemas import ComplaintCreate, ComplaintResponse, ComplaintDetailResponse, CategoryResponse
from ..auth import get_current_user
from ..patterns.facade import ComplaintFacade

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.get("/map", response_model=List[ComplaintResponse])
async def map_complaints(db: AsyncSession = Depends(get_db)):
    facade = ComplaintFacade(db)
    items = await facade.get_all_complaints(skip=0, limit=500)
    return [ComplaintResponse.model_validate(c) for c in items if c.lat and c.lng]


@router.get("/recent", response_model=List[ComplaintResponse])
async def recent_complaints(
    limit: int = 5,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facade = ComplaintFacade(db)
    items = await facade.get_all_complaints(skip=0, limit=limit)
    return [ComplaintResponse.model_validate(c) for c in items]


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return [CategoryResponse.model_validate(c) for c in result.scalars().all()]


@router.get("/my", response_model=List[ComplaintResponse])
async def my_complaints(
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facade = ComplaintFacade(db)
    items = await facade.get_user_complaints(user.id, skip, limit)
    return [ComplaintResponse.model_validate(c) for c in items]


@router.get("/track/{ticket}", response_model=ComplaintDetailResponse)
async def track(ticket: str, db: AsyncSession = Depends(get_db)):
    facade = ComplaintFacade(db)
    complaint = await facade.get_complaint_by_ticket(ticket.upper())
    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")
    return ComplaintDetailResponse.model_validate(complaint)


@router.post("", response_model=ComplaintResponse, status_code=201)
async def create_complaint(
    data: ComplaintCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facade = ComplaintFacade(db)
    complaint = await facade.submit_complaint(user.id, data.model_dump())
    return ComplaintResponse.model_validate(complaint)


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
async def get_complaint(
    complaint_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facade = ComplaintFacade(db)
    complaint = await facade.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")
    if not user.is_admin and complaint.user_id != user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return ComplaintDetailResponse.model_validate(complaint)
