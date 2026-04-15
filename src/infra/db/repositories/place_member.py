from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models.place import Place
from src.infra.db.models.place_member import PlaceMember, PlaceRole

from .base import BaseRepository


class PlaceMemberRepository(BaseRepository[PlaceMember]):
    def __init__(self, session: AsyncSession):
        super().__init__(PlaceMember, session)

    async def delete_all_by_place(self, place_id: UUID) -> Sequence[UUID]:
        result = await self.session.execute(
            delete(PlaceMember)
            .where(PlaceMember.place_id == place_id)
            .returning(PlaceMember.user_id)
        )
        await self.session.flush()
        return result.scalars().all()

    async def list_places_with_roles(self, user_id: UUID) -> list[tuple[Place, PlaceRole]]:
        query = (
            select(Place, PlaceMember.role)
            .join(PlaceMember, Place.id == PlaceMember.place_id)
            .where(PlaceMember.user_id == user_id)
        )
        result = await self.session.execute(query)
        return [(row[0], row[1]) for row in result.all()]
