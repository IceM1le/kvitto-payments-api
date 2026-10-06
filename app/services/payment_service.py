from typing import Final


VALID_INSTALLMENT_MONTHS: Final[set[int]] = {3, 6, 12}

ALLOWED_STATUS_TRANSITIONS: Final[dict[str, set[str]]] = {
    "pending": {"succeeded", "failed"},
    "succeeded": {"refunded"},
}


class InvalidPromoCodeError(Exception):
    """Некорректный промокод."""


class InvalidInstallmentMonthsError(Exception):
    """Некорректный срок рассрочки."""


def calculate_discount(
    price: int,
    promo_code: str | None,
) -> tuple[int, int]:
    """
    Рассчитывает итоговую сумму и скидку по промокоду.

    Возвращает кортеж:
    (amount, discount)
    """

    if promo_code is None:
        return price, 0

    if promo_code.upper() != "KVITTO10":
        raise InvalidPromoCodeError("Некорректный промокод.")

    discount = price * 10 // 100
    amount = price - discount

    return amount, discount


def calculate_installment_schedule(
    amount: int,
    months: int,
) -> list[int]:
    """Формирует график платежей для рассрочки."""

    if months not in VALID_INSTALLMENT_MONTHS:
        raise InvalidInstallmentMonthsError(
            "Допустимые сроки рассрочки: 3, 6 или 12 месяцев."
        )

    base = amount // months
    remainder = amount % months

    schedule = [
        base + 1 if index < remainder else base
        for index in range(months)
    ]

    return schedule


def is_valid_status_transition(
    current_status: str,
    new_status: str,
) -> bool:
    """Проверяет допустимость перехода статуса."""

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    return new_status in allowed_statuses