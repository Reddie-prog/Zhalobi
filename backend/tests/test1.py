import sys
import os

# Добавляем папку backend в путь поиска
sys.path.insert(0, '/Users/anastasiya/Zhalobi/backend')

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import Base
from app.models import Complaint, User, Category
from app.services.complaint_service import ComplaintService


@pytest.mark.asyncio
async def test_get_stats_with_sample_data():
    """Тест проверяет, что get_stats правильно считает количество жалоб"""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        # Создаём пользователя с обязательным password_hash
        user = User(
            id=1,
            email="test@example.com",
            password_hash="fake_password_hash_for_testing",
            full_name="Test User"
        )
        
        # Создаём категорию
        category = Category(
            id=1,
            name="Test Category"
        )
        
        db.add(user)
        db.add(category)
        await db.commit()

        # Создаём тестовые жалобы
        complaint1 = Complaint(
            ticket_number="TEST-001",
            user_id=1,
            category_id=1,
            title="Тест 1",
            description="Описание теста 1",
            address="ул. Тестовая, 1",
            status="new",
            priority="medium"
        )
        complaint2 = Complaint(
            ticket_number="TEST-002",
            user_id=1,
            category_id=1,
            title="Тест 2",
            description="Описание теста 2",
            address="ул. Тестовая, 2",
            status="resolved",
            priority="medium"
        )
        complaint3 = Complaint(
            ticket_number="TEST-003",
            user_id=1,
            category_id=1,
            title="Тест 3",
            description="Описание теста 3",
            address="ул. Тестовая, 3",
            status="closed",
            priority="medium"
        )

        db.add(complaint1)
        db.add(complaint2)
        db.add(complaint3)
        await db.commit()

        service = ComplaintService(db)
        stats = await service.get_stats()

        # Проверяем результаты
        assert stats["total_complaints"] == 3
        assert stats["new_complaints"] == 1
        assert stats["resolved_complaints"] == 1
        assert stats["closed_complaints"] == 1

        print("✅ Тест пройден!")