from pydantic import BaseModel, field_validator
import uuid
from decimal import Decimal
from .package_type import PackageTypeBase


class PackageCreate(BaseModel):
    name: str
    weight_kg: Decimal
    type_id: uuid.UUID = None
    contents_value_usd: Decimal

    @field_validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()

    @field_validator("weight_kg")
    def weight_reasonable(cls, v):
        if v <= 0:
            raise ValueError("Вес должен быть положительным")
        if v > 1000:
            raise ValueError("Вес не может превышать 1000 кг")
        return v

    @field_validator("contents_value_usd")
    def value_reasonable(cls, v):
        if v <= 0:
            raise ValueError("Стоимость должна быть положительной")
        if v > 1000000:
            raise ValueError("Стоимость не может превышать 1,000,000 USD")
        return v


class PackageCreateResponse(BaseModel):
    id: uuid.UUID
    name: str
    weight_kg: Decimal
    type_id: uuid.UUID | None = None
    contents_value_usd: Decimal

    class Config:
        from_attributes = True


class PackageResponse(BaseModel):
    id: uuid.UUID
    name: str
    weight_kg: Decimal
    contents_value_usd: Decimal
    delivery_cost_rub: Decimal | str | None = None
    package_type: PackageTypeBase | None = None

    @property
    def is_cost_calculated(self) -> bool:
        return self.delivery_cost_rub is not None

    class Config:
        orm_mode = True


class PackageListResponse(BaseModel):
    packages: list[PackageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True
