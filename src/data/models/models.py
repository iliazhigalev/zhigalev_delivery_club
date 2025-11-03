import uuid
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Numeric,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class PackageType(Base):
    __tablename__ = "package_types"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    packages = relationship("Package", back_populates="package_type", lazy="selectin")

    def __repr__(self):
        return f"<PackageType id={self.id} name={self.name!r}>"


class Package(Base):
    __tablename__ = "packages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    weight_kg = Column(Numeric(10, 3), nullable=False)
    type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("package_types.id", ondelete="RESTRICT"),
        nullable=True,
    )
    contents_value_usd = Column(Numeric(12, 2), nullable=False)
    delivery_cost_rub = Column(Numeric(14, 2), nullable=True)
    owner_session_id = Column(String(128), nullable=False, index=True)

    package_type = relationship("PackageType", back_populates="packages", lazy="joined")

    __table_args__ = (
        Index("ix_packages_owner_type", "owner_session_id", "type_id"),
        Index("ix_packages_owner_delivery", "owner_session_id", "delivery_cost_rub"),
    )

    def __repr__(self):
        return (
            f"<Package id={self.id} name={self.name!r} owner={self.owner_session_id}>"
        )
