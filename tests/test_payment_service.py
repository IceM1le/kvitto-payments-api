import pytest

from app.services.payment_service import (
    InvalidInstallmentMonthsError,
    InvalidPromoCodeError,
    calculate_discount,
    calculate_installment_schedule,
    is_valid_status_transition,
)


def test_calculate_discount_without_promo() -> None:
    """Проверяет расчёт без промокода."""

    amount, discount = calculate_discount(
        price=1990000,
        promo_code=None,
    )

    assert amount == 1990000
    assert discount == 0


def test_calculate_discount_with_valid_promo() -> None:
    """Проверяет расчёт с валидным промокодом."""

    amount, discount = calculate_discount(
        price=1990000,
        promo_code="KVITTO10",
    )

    assert discount == 199000
    assert amount == 1791000


def test_calculate_discount_with_lowercase_promo() -> None:
    """Проверяет регистронезависимость промокода."""

    amount, discount = calculate_discount(
        price=1990000,
        promo_code="kvitto10",
    )

    assert discount == 199000
    assert amount == 1791000


def test_calculate_discount_with_invalid_promo() -> None:
    """Проверяет ошибку при неизвестном промокоде."""

    with pytest.raises(InvalidPromoCodeError):
        calculate_discount(
            price=1990000,
            promo_code="INVALID",
        )


def test_installment_schedule_3_months() -> None:
    """Проверяет график на 3 месяца."""

    amount = 1990000

    schedule = calculate_installment_schedule(
        amount=amount,
        months=3,
    )

    assert schedule == [663334, 663333, 663333]
    assert sum(schedule) == amount


def test_installment_schedule_6_months() -> None:
    """Проверяет график на 6 месяцев."""

    amount = 1990000

    schedule = calculate_installment_schedule(
        amount=amount,
        months=6,
    )

    assert len(schedule) == 6
    assert sum(schedule) == amount


def test_installment_schedule_12_months() -> None:
    """Проверяет график на 12 месяцев."""

    amount = 1990000

    schedule = calculate_installment_schedule(
        amount=amount,
        months=12,
    )

    assert len(schedule) == 12
    assert sum(schedule) == amount


def test_installment_schedule_invalid_months() -> None:
    """Проверяет ошибку для недопустимого срока рассрочки."""

    with pytest.raises(InvalidInstallmentMonthsError):
        calculate_installment_schedule(
            amount=1990000,
            months=5,
        )


def test_pending_to_succeeded_is_allowed() -> None:
    """Проверяет разрешённый переход pending -> succeeded."""

    assert is_valid_status_transition(
        "pending",
        "succeeded",
    )


def test_pending_to_failed_is_allowed() -> None:
    """Проверяет разрешённый переход pending -> failed."""

    assert is_valid_status_transition(
        "pending",
        "failed",
    )


def test_succeeded_to_refunded_is_allowed() -> None:
    """Проверяет разрешённый переход succeeded -> refunded."""

    assert is_valid_status_transition(
        "succeeded",
        "refunded",
    )


def test_pending_to_refunded_is_forbidden() -> None:
    """Проверяет запрещённый переход pending -> refunded."""

    assert not is_valid_status_transition(
        "pending",
        "refunded",
    )


def test_failed_to_succeeded_is_forbidden() -> None:
    """Проверяет запрещённый переход failed -> succeeded."""

    assert not is_valid_status_transition(
        "failed",
        "succeeded",
    )


def test_failed_to_refunded_is_forbidden() -> None:
    """Проверяет запрещённый переход failed -> refunded."""

    assert not is_valid_status_transition(
        "failed",
        "refunded",
    )


def test_refunded_to_pending_is_forbidden() -> None:
    """Проверяет запрещённый переход refunded -> pending."""

    assert not is_valid_status_transition(
        "refunded",
        "pending",
    )


def test_refunded_to_succeeded_is_forbidden() -> None:
    """Проверяет запрещённый переход refunded -> succeeded."""

    assert not is_valid_status_transition(
        "refunded",
        "succeeded",
    )
