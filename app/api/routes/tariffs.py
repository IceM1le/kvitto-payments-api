from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Tariff
from app.schemas.tariff import TariffResponse

router = APIRouter(
    prefix="/tariffs",
    tags=["Tariffs"],
)


@router.get(
    "",
    response_model=list[TariffResponse],
)
async def get_tariffs(
    db: AsyncSession = Depends(get_db),
) -> list[Tariff]:
    """Возвращает список тарифов."""

    result = await db.execute(
        select(Tariff).order_by(Tariff.id)
    )

    return list(result.scalars().all())
