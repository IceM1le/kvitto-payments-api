from typing import Literal

from pydantic import BaseModel


class WebhookRequest(BaseModel):
    """Схема банковского вебхука."""

    payment_id: int
    status: Literal[
        "succeeded",
        "failed",
        "refunded",
    ]
