from pydantic import BaseModel
import uuid


class PackageTypeBase(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class PackageTypeResponse(BaseModel):
    id: uuid.UUID


class PackageTypeList(BaseModel):
    package_types: list[PackageTypeResponse]

    class Config:
        from_attributes = True
