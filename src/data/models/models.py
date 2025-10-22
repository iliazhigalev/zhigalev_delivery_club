import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()


class PackageType(Base):
    """
    Хранит тип посылки

    Поля:
        id   — уникальный идентификатор типа посылки (Primary Key)
        name — название типа посылки (уникальное, строка до 50 символов)
    """

    __tablename__ = "package_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)

    packages = relationship("Package", back_populates="package_type", lazy="selectin")

    def __repr__(self):
        return f"<PackageType id={self.id} name={self.name!r}>"


class Package(Base):
    """
    Хранит данные о конкретной посылке, зарегистрированной пользователем (по сессии).

    Поля:
        id                 — UUID посылки
        name               — название посылки
        weight_kg          — вес в килограммах
        type_id            — ссылка на тип посылки (FK → PackageType)
        contents_value_usd — стоимость содержимого в долларах
        delivery_cost_rub  — рассчитанная стоимость доставки в рублях
        company_id         — id транспортной компании, если посылка закреплена
        owner_session_id   — уникальный идентификатор сессии пользователя
        created_at         — дата регистрации посылки
        claimed_at         — дата, когда посылка была “захвачена” компанией
    """

    __tablename__ = "packages"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    weight_kg = Column(Numeric(10, 3), nullable=False)
    type_id = Column(
        Integer, ForeignKey("package_types.id", ondelete="RESTRICT"), nullable=False
    )
    contents_value_usd = Column(Numeric(12, 2), nullable=False)
    delivery_cost_rub = Column(Numeric(14, 2), nullable=True)
    company_id = Column(Integer, nullable=True)
    owner_session_id = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    claimed_at = Column(DateTime(timezone=True), nullable=True)

    package_type = relationship("PackageType", back_populates="packages", lazy="joined")

    __table_args__ = (
        Index("ix_packages_owner_type", "owner_session_id", "type_id"),
        Index("ix_packages_owner_delivery", "owner_session_id", "delivery_cost_rub"),
    )

    def __repr__(self):
        return (
            f"<Package id={self.id} name={self.name!r} owner={self.owner_session_id}>"
        )
