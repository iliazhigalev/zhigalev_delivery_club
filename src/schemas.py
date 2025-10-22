from pydantic import BaseModel, Field, condecimal
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

Money = condecimal(max_digits=14, decimal_places=2)


class PackageCreate(BaseModel):
    """
    Схема входных данных для регистрации посылки.
    """

    name: str = Field(..., min_length=1, max_length=255)
    weight_kg: condecimal(max_digits=10, decimal_places=3)
    type_id: int = Field(..., gt=0)
    contents_value_usd: condecimal(max_digits=12, decimal_places=2)


class PackageTypeOut(BaseModel):
    """
    Схема вывода типа посылки.
    """

    id: int
    name: str

    class Config:
        orm_mode = True


class PackageOut(BaseModel):
    """
    Схема вывода информации о посылке.
    """

    id: UUID
    name: str
    weight_kg: Decimal
    type_id: int
    type_name: str
    contents_value_usd: Decimal
    delivery_cost_rub: Optional[Decimal]
    company_id: Optional[int]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class PaginatedPackages(BaseModel):
    """
    Схема при запросе посылки или списка посылки с пагинацией
    """

    total: int
    page: int
    size: int
    items: list[PackageOut]
