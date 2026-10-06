from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.base import Base
from app.db.seed import seed_tariffs
from app.db.session import AsyncSessionLocal, engine

# Импортируем модели, чтобы они зарегистрировались в metadata.
from app.models import Payment, Tariff  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""

    # Создаём таблицы при запуске приложения.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Идемпотентно создаём тарифы по умолчанию.
    async with AsyncSessionLocal() as session:
        await seed_tariffs(session)

    yield


app = FastAPI(
    title="Kvitto Payments",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}