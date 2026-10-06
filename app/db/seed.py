from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tariff

DEFAULT_TARIFFS = [
    {"title": "basic", "price": 990000},
    {"title": "standard", "price": 1990000},
    {"title": "premium", "price": 2990000},
]


async def seed_tariffs(session: AsyncSession) -> None:
    """Создание тарифов по умолчанию, если они не существуют."""
    for tariff_data in DEFAULT_TARIFFS:
        stmt = select(Tariff).where(
            Tariff.title == tariff_data["title"]
        )

        result = await session.execute(stmt)
        tariff = result.scalar_one_or_none()

        if tariff is None:
            session.add(Tariff(**tariff_data))

    await session.commit()