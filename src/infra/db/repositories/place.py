from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models.place import Place

from .base import BaseRepository


class PlaceRepository(BaseRepository[Place]):
    def __init__(self, session: AsyncSession):
        super().__init__(Place, session)
