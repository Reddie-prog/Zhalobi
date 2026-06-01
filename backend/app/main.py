import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from .database import create_tables, AsyncSessionLocal
from .api.auth import router as auth_router
from .api.complaints import router as complaints_router
from .api.admin import router as admin_router
from .api.stats import router as stats_router
from .background.handlers import setup_handlers
from .background.escalation import escalation_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def seed_data():
    from .models import Category, User
    from .auth import hash_password

    async with AsyncSessionLocal() as db:
        cat_count = await db.scalar(select(func.count()).select_from(Category))
        if not cat_count:
            categories = [
                Category(name="Водоснабжение", description="Проблемы с водоснабжением и канализацией",
                         icon="💧", auto_escalation_hours=48),
                Category(name="Отопление", description="Проблемы с отоплением и теплоснабжением",
                         icon="🔥", auto_escalation_hours=24),
                Category(name="Электроснабжение", description="Аварии и перебои в электроснабжении",
                         icon="⚡", auto_escalation_hours=24),
                Category(name="Лифты", description="Неисправность лифтового оборудования",
                         icon="🛗", auto_escalation_hours=12),
                Category(name="Уборка территории", description="Уборка придомовой территории",
                         icon="🧹", auto_escalation_hours=72),
                Category(name="Дороги и тротуары", description="Ямы, трещины, повреждения дорог",
                         icon="🛣️", auto_escalation_hours=96),
                Category(name="Освещение", description="Неисправность уличного освещения",
                         icon="💡", auto_escalation_hours=72),
                Category(name="Другое", description="Прочие коммунальные проблемы",
                         icon="🏠", auto_escalation_hours=72),
            ]
            for c in categories:
                db.add(c)

        admin = await db.scalar(select(User).where(User.is_admin.is_(True)))
        if not admin:
            db.add(User(
                email="admin@zhalobi.ru",
                password_hash=hash_password("admin123"),
                full_name="Администратор системы",
                is_admin=True,
            ))

        await db.commit()
    logger.info("Seed data applied")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Жалоби ЖКХ platform...")
    await create_tables()
    await seed_data()
    setup_handlers()

    task = asyncio.create_task(escalation_loop())
    logger.info("Background escalation task started")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown complete")


app = FastAPI(
    title="Жалоби ЖКХ — API",
    description="Асинхронная платформа сбора и обработки жалоб ЖКХ. "
                "Паттерны: Facade, Observer, Command.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(complaints_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(stats_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Жалоби ЖКХ", "version": "1.0.0"}
