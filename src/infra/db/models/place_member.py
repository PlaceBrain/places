import enum

from sqlalchemy import UUID, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.core.types import IDType

from .base import Base


class PlaceRole(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class PlaceMember(Base):
    __tablename__ = "place_members"

    place_id: Mapped[IDType] = mapped_column(UUID, ForeignKey("places.id"), nullable=False)
    user_id: Mapped[IDType] = mapped_column(UUID, nullable=False)
    role: Mapped[PlaceRole] = mapped_column(
        SQLAlchemyEnum(PlaceRole), nullable=False, default=PlaceRole.VIEWER
    )

    __table_args__ = (UniqueConstraint("place_id", "user_id"),)
