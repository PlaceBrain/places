import logging
from uuid import UUID

from src.infra.db.models.place import Place
from src.infra.db.models.place_member import PlaceMember, PlaceRole
from src.infra.db.uow import UnitOfWork

logger = logging.getLogger(__name__)


class PlacesService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def _get_member_or_fail(self, user_id: UUID, place_id: UUID) -> PlaceMember:
        member = await self.uow.place_member_repository.get_one_or_none(
            place_id=place_id, user_id=user_id
        )
        if not member:
            raise PermissionError("User is not a member of this place")
        return member

    async def create_place(self, user_id: UUID, name: str, description: str) -> str:
        async with self.uow:
            place = await self.uow.place_repository.create(name=name, description=description)
            await self.uow.place_member_repository.create(
                place_id=place.id, user_id=user_id, role=PlaceRole.OWNER
            )
            return str(place.id)

    async def get_place(self, user_id: UUID, place_id: UUID) -> tuple[Place, PlaceRole]:
        async with self.uow:
            member = await self._get_member_or_fail(user_id, place_id)
            place = await self.uow.place_repository.get_by_id(place_id)
            if not place:
                raise ValueError("Place not found")
            return place, member.role

    async def list_places(self, user_id: UUID) -> list[tuple[Place, PlaceRole]]:
        async with self.uow:
            return await self.uow.place_member_repository.list_places_with_roles(user_id)

    async def update_place(self, user_id: UUID, place_id: UUID, name: str, description: str) -> str:
        async with self.uow:
            member = await self._get_member_or_fail(user_id, place_id)
            if member.role not in (PlaceRole.OWNER, PlaceRole.ADMIN):
                raise PermissionError("Only owner or admin can update a place")
            await self.uow.place_repository.update(place_id, name=name, description=description)
            return str(place_id)

    async def delete_place(self, user_id: UUID, place_id: UUID) -> bool:
        async with self.uow:
            member = await self._get_member_or_fail(user_id, place_id)
            if member.role != PlaceRole.OWNER:
                raise PermissionError("Only owner can delete a place")
            # Delete all members atomically
            await self.uow.place_member_repository.delete_all_by_place(place_id)
            place = await self.uow.place_repository.get_by_id(place_id)
            if not place:
                raise ValueError("Place not found")
            await self.uow.place_repository.delete(place)
            return True

    async def add_member(
        self, user_id: UUID, place_id: UUID, target_user_id: UUID, role: PlaceRole
    ) -> bool:
        async with self.uow:
            member = await self._get_member_or_fail(user_id, place_id)
            if role == PlaceRole.OWNER:
                raise PermissionError("Cannot add a member with owner role")
            if member.role == PlaceRole.ADMIN and role != PlaceRole.VIEWER:
                raise PermissionError("Admin can only add viewers")
            if member.role not in (PlaceRole.OWNER, PlaceRole.ADMIN):
                raise PermissionError("Only owner or admin can add members")
            existing = await self.uow.place_member_repository.get_one_or_none(
                place_id=place_id, user_id=target_user_id
            )
            if existing:
                raise ValueError("User is already a member of this place")
            await self.uow.place_member_repository.create(
                place_id=place_id, user_id=target_user_id, role=role
            )
            return True

    async def remove_member(self, user_id: UUID, place_id: UUID, target_user_id: UUID) -> bool:
        async with self.uow:
            member = await self._get_member_or_fail(user_id, place_id)
            if member.role not in (PlaceRole.OWNER, PlaceRole.ADMIN):
                raise PermissionError("Only owner or admin can remove members")
            target = await self.uow.place_member_repository.get_one_or_none(
                place_id=place_id, user_id=target_user_id
            )
            if not target:
                raise ValueError("Target user is not a member of this place")
            if target.role == PlaceRole.OWNER:
                raise PermissionError("Cannot remove the owner")
            if member.role == PlaceRole.ADMIN and target.role != PlaceRole.VIEWER:
                raise PermissionError("Admin can only remove viewers")
            await self.uow.place_member_repository.delete(target)
            return True

    async def update_member_role(
        self, user_id: UUID, place_id: UUID, target_user_id: UUID, role: PlaceRole
    ) -> bool:
        async with self.uow:
            member = await self._get_member_or_fail(user_id, place_id)
            if member.role != PlaceRole.OWNER:
                raise PermissionError("Only owner can update member roles")
            if role == PlaceRole.OWNER:
                raise PermissionError("Cannot assign owner role")
            target = await self.uow.place_member_repository.get_one_or_none(
                place_id=place_id, user_id=target_user_id
            )
            if not target:
                raise ValueError("Target user is not a member of this place")
            if target.role == PlaceRole.OWNER:
                raise PermissionError("Cannot change the owner's role")
            await self.uow.place_member_repository.update(target.id, role=role)
            return True

    async def list_members(self, user_id: UUID, place_id: UUID) -> list[PlaceMember]:
        async with self.uow:
            await self._get_member_or_fail(user_id, place_id)
            members = await self.uow.place_member_repository.get_all(place_id=place_id)
            return list(members)
