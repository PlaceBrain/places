from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models.place_member import PlaceMember

from .base import BaseRepository


class PlaceMemberRepository(BaseRepository[PlaceMember]):
    def __init__(self, session: AsyncSession):
        super().__init__(PlaceMember, session)
