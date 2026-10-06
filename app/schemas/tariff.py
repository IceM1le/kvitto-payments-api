from pydantic import BaseModel, ConfigDict


class TariffResponse(BaseModel):
    """Схема ответа с тарифом."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: int