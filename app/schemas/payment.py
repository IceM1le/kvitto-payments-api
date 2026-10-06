from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator


class PaymentCreateRequest(BaseModel):
    """Схема создания платежа."""

    tariff_id: int
    email: EmailStr
    method: Literal["card", "sbp", "installment"]

    installment_months: int | None = None
    promo_code: str | None = None

    @model_validator(mode="after")
    def validate_installment(self) -> "PaymentCreateRequest":
        """Проверяет параметры рассрочки."""

        if self.method != "installment":
            return self

        if self.installment_months is None:
            raise ValueError(
                "Для рассрочки необходимо указать installment_months."
            )

        if self.installment_months not in {3, 6, 12}:
            raise ValueError(
                "Допустимые сроки рассрочки: 3, 6 или 12 месяцев."
            )

        return self


class PaymentResponse(BaseModel):
    """Схема ответа с платежом."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    tariff_id: int

    amount: int
    discount: int

    method: str

    installment_months: int | None
    schedule: list[int] | None

    email: str
    created_at: datetime
