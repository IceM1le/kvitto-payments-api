from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Payment, Tariff
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
)
from app.services.payment_service import (
    InvalidInstallmentMonthsError,
    InvalidPromoCodeError,
    calculate_discount,
    calculate_installment_schedule,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payload: PaymentCreateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
) -> Payment:
    """Создаёт новый платёж."""

    # Проверяем идемпотентность до любых расчётов и создания записи.
    if idempotency_key:
        existing_payment_result = await db.execute(
            select(Payment).where(
                Payment.idempotency_key == idempotency_key
            )
        )

        existing_payment = existing_payment_result.scalar_one_or_none()

        if existing_payment is not None:
            response.status_code = status.HTTP_200_OK
            return existing_payment

    tariff_result = await db.execute(
        select(Tariff).where(
            Tariff.id == payload.tariff_id
        )
    )

    tariff = tariff_result.scalar_one_or_none()

    if tariff is None:
        raise HTTPException(
            status_code=404,
            detail="Тариф не найден.",
        )

    try:
        amount, discount = calculate_discount(
            price=tariff.price,
            promo_code=payload.promo_code,
        )
    except InvalidPromoCodeError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    schedule: list[int] | None = None

    if payload.method == "installment":
        try:
            schedule = calculate_installment_schedule(
                amount=amount,
                months=payload.installment_months,
            )
        except InvalidInstallmentMonthsError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

    payment = Payment(
        status="pending",
        tariff_id=tariff.id,
        amount=amount,
        discount=discount,
        method=payload.method,
        installment_months=payload.installment_months,
        schedule=schedule,
        email=str(payload.email),
        idempotency_key=idempotency_key,
    )

    db.add(payment)

    await db.commit()
    await db.refresh(payment)

    return payment


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
) -> Payment:
    """Возвращает платёж по идентификатору."""

    payment = await db.get(
        Payment,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Платёж не найден.",
        )

    return payment