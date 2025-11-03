from pydantic import BaseModel, field_validator
from uuid import UUID


class PackageFilter(BaseModel):
    type_id: UUID | None = None
    has_calculated_cost: bool | None = None


class PaginationParams(BaseModel):
    page: int | None = 1
    page_size: int | None = 100

    @field_validator("page_size")
    def validate_page_size(cls, value):
        if value > 100:
            raise ValueError("The page size cannot exceed 100")
        return value
