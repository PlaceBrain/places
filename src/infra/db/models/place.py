from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Place(Base):
    __tablename__ = "places"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
