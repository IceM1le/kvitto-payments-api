from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Payment
from app.schemas.webhook import WebhookRequest
from app.services.payment_service import (
    is_valid_status_transition,
)

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@router.post("/bank")
async def bank_webhook(
    payload: WebhookRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Обрабатывает уведомление банка."""

    payment = await db.get(
        Payment,
        payload.payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Платёж не найден.",
        )

    if not is_valid_status_transition(
        payment.status,
        payload.status,
    ):
        raise HTTPException(
            status_code=409,
            detail="Недопустимый переход статуса.",
        )

    payment.status = payload.status

    await db.commit()
    await db.refresh(payment)

    return {"status": "ok"}