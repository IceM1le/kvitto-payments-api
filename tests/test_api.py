from collections.abc import AsyncGenerator

import hashlib
import hmac
import json
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Payment, Tariff


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_payment(
    client: AsyncClient,
    email: str,
) -> int:
    """Создаёт тестовый платёж."""

    response = await client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": email,
            "method": "card",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Возвращает тестовую сессию БД."""

    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Создаёт тестовый HTTP-клиент."""

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        session.add(
            Tariff(
                title="standard",
                price=1990000,
            )
        )
        await session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate(
    client: AsyncClient,
) -> None:
    """Проверяет защиту от создания дублей."""

    payload = {
        "tariff_id": 1,
        "email": "user@example.com",
        "method": "card",
    }

    headers = {
        "Idempotency-Key": "test-key-123",
    }

    first_response = await client.post(
        "/payments",
        json=payload,
        headers=headers,
    )

    assert first_response.status_code == 201

    first_payment = first_response.json()

    second_response = await client.post(
        "/payments",
        json=payload,
        headers=headers,
    )

    assert second_response.status_code == 200

    second_payment = second_response.json()

    assert first_payment["id"] == second_payment["id"]

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(func.count(Payment.id))
        )

        payments_count = result.scalar_one()

    assert payments_count == 1


@pytest.mark.asyncio
async def test_invalid_transition_does_not_change_status(
    client: AsyncClient,
) -> None:
    """Проверяет, что запрещённый переход не меняет статус."""

    create_response = await client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
        },
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    body = json.dumps(
        {
            "payment_id": payment_id,
            "status": "refunded",
        }
    ).encode()

    signature = hmac.new(
        b"test-secret",
        body,
        hashlib.sha256,
    ).hexdigest()

    webhook_response = await client.post(
        "/webhooks/bank",
        content=body,
        headers={
            "X-Signature": signature,
            "Content-Type": "application/json",
        },
    )

    assert webhook_response.status_code == 409
    assert webhook_response.json() == {
        "error": "invalid_transition"
    }

    payment_response = await client.get(
        f"/payments/{payment_id}"
    )

    assert payment_response.status_code == 200
    assert payment_response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_get_nonexistent_payment_returns_404(
    client: AsyncClient,
) -> None:
    """Проверяет получение несуществующего платежа."""

    response = await client.get(
        "/payments/999999"
    )

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_webhook_valid_signature(
    client: AsyncClient,
) -> None:
    """Проверяет вебхук с корректной подписью."""

    create_response = await client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
        },
    )

    payment_id = create_response.json()["id"]

    body = json.dumps(
        {
            "payment_id": payment_id,
            "status": "succeeded",
        }
    ).encode()

    signature = hmac.new(
        b"test-secret",
        body,
        hashlib.sha256,
    ).hexdigest()

    response = await client.post(
        "/webhooks/bank",
        content=body,
        headers={
            "X-Signature": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_invalid_signature(
    client: AsyncClient,
) -> None:
    """Проверяет вебхук с неверной подписью."""

    create_response = await client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
        },
    )

    payment_id = create_response.json()["id"]

    response = await client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment_id,
            "status": "succeeded",
        },
        headers={
            "X-Signature": "invalid-signature",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": "invalid_signature",
    }


@pytest.mark.asyncio
async def test_webhook_missing_signature(
    client: AsyncClient,
) -> None:
    """Проверяет вебхук без подписи."""

    create_response = await client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "user@example.com",
            "method": "card",
        },
    )

    payment_id = create_response.json()["id"]

    response = await client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment_id,
            "status": "succeeded",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": "invalid_signature",
    }

@pytest.mark.asyncio
async def test_get_payments_without_filters(
    client: AsyncClient,
) -> None:
    """Проверяет получение всех платежей."""

    await create_payment(
        client,
        "user1@example.com",
    )

    await create_payment(
        client,
        "user2@example.com",
    )

    response = await client.get(
        "/payments",
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_get_payments_filter_by_email(
    client: AsyncClient,
) -> None:
    """Проверяет фильтрацию по email."""

    await create_payment(
        client,
        "user1@example.com",
    )

    await create_payment(
        client,
        "user2@example.com",
    )

    response = await client.get(
        "/payments",
        params={
            "email": "user1@example.com",
        },
    )

    assert response.status_code == 200

    payments = response.json()

    assert len(payments) == 1
    assert payments[0]["email"] == "user1@example.com"

@pytest.mark.asyncio
async def test_get_payments_filter_by_status(
    client: AsyncClient,
) -> None:
    """Проверяет фильтрацию по статусу."""

    first_payment_id = await create_payment(
        client,
        "user1@example.com",
    )

    second_payment_id = await create_payment(
        client,
        "user2@example.com",
    )

    async with TestSessionLocal() as session:
        payment = await session.get(
            Payment,
            first_payment_id,
        )

        payment.status = "succeeded"

        await session.commit()

    response = await client.get(
        "/payments",
        params={
            "status": "succeeded",
        },
    )

    assert response.status_code == 200

    payments = response.json()

    assert len(payments) == 1
    assert payments[0]["id"] == first_payment_id

    _ = second_payment_id

@pytest.mark.asyncio
async def test_get_payments_filter_by_email_and_status(
    client: AsyncClient,
) -> None:
    """Проверяет одновременную фильтрацию."""

    target_id = await create_payment(
        client,
        "user1@example.com",
    )

    second_id = await create_payment(
        client,
        "user1@example.com",
    )

    third_id = await create_payment(
        client,
        "user2@example.com",
    )

    async with TestSessionLocal() as session:
        payment = await session.get(
            Payment,
            target_id,
        )

        payment.status = "succeeded"

        await session.commit()

    response = await client.get(
        "/payments",
        params={
            "email": "user1@example.com",
            "status": "pending",
        },
    )

    assert response.status_code == 200

    payments = response.json()

    assert len(payments) == 1
    assert payments[0]["id"] == second_id

    _ = third_id