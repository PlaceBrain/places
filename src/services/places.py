import logging
from uuid import UUID

from faststream.kafka import KafkaBroker

from src.core.dto import PlaceMemberDTO, PlaceWithRoleDTO
from src.core.exceptions import AlreadyExistsError, NotFoundError, PermissionDeniedError
from src.infra.db.models.place_member import PlaceRole
from src.infra.db.uow import UnitOfWork

logger = logging.getLogger(__name__)

PLACES_EVENTS_TOPIC = "places.events"


class PlacesService:
    def __init__(self, uow: UnitOfWork, broker: KafkaBroker) -> None:
        self.uow = uow
        self.broker = broker

    async def _publish_event(self, event: dict, key: str) -> None:
        await self.broker.publish(event, topic=PLACES_EVENTS_TOPIC, key=key.encode())

    async def _get_member_or_fail(self, user_id: UUID, place_id: UUID) -> PlaceRole:
        member = await self.uow.place_member_repository.get_one_or_none(
            place_id=place_id, user_id=user_id
        )
        if not member:
            raise PermissionDeniedError("User is not a member of this place")
        return member.role

    async def create_place(self, user_id: UUID, name: str, description: str) -> str:
        place = await self.uow.place_repository.create(name=name, description=description)
        await self.uow.place_member_repository.create(
            place_id=place.id, user_id=user_id, role=PlaceRole.OWNER
        )
        await self._publish_event(
            {
                "event_type": "member.added",
                "place_id": str(place.id),
                "user_id": str(user_id),
                "role": PlaceRole.OWNER.value,
            },
            key=f"{place.id}:{user_id}",
        )
        return str(place.id)

    async def get_place(self, user_id: UUID, place_id: UUID) -> PlaceWithRoleDTO:
        role = await self._get_member_or_fail(user_id, place_id)
        place = await self.uow.place_repository.get_by_id(place_id)
        if not place:
            raise NotFoundError("Place not found")
        return PlaceWithRoleDTO(
            id=place.id, name=place.name, description=place.description, role=role
        )

    async def list_places(self, user_id: UUID) -> list[PlaceWithRoleDTO]:
        rows = await self.uow.place_member_repository.list_places_with_roles(user_id)
        return [
            PlaceWithRoleDTO(id=place.id, name=place.name, description=place.description, role=role)
            for place, role in rows
        ]

    async def update_place(self, user_id: UUID, place_id: UUID, name: str, description: str) -> str:
        role = await self._get_member_or_fail(user_id, place_id)
        if role not in (PlaceRole.OWNER, PlaceRole.ADMIN):
            raise PermissionDeniedError("Only owner or admin can update a place")
        await self.uow.place_repository.update(place_id, name=name, description=description)
        return str(place_id)

    async def delete_place(self, user_id: UUID, place_id: UUID) -> bool:
        role = await self._get_member_or_fail(user_id, place_id)
        if role != PlaceRole.OWNER:
            raise PermissionDeniedError("Only owner can delete a place")
        members = await self.uow.place_member_repository.get_all(place_id=place_id)
        member_ids = [m.user_id for m in members]
        await self.uow.place_member_repository.delete_all_by_place(place_id)
        place = await self.uow.place_repository.get_by_id(place_id)
        if not place:
            raise NotFoundError("Place not found")
        await self.uow.place_repository.delete(place)
        await self._publish_event(
            {
                "event_type": "place.deleted",
                "place_id": str(place_id),
                "member_ids": [str(m) for m in member_ids],
            },
            key=str(place_id),
        )
        for member_id in member_ids:
            await self.broker.publish(
                None, topic=PLACES_EVENTS_TOPIC, key=f"{place_id}:{member_id}".encode()
            )
        return True

    async def add_member(
        self, user_id: UUID, place_id: UUID, target_user_id: UUID, role: PlaceRole
    ) -> bool:
        member_role = await self._get_member_or_fail(user_id, place_id)
        if role == PlaceRole.OWNER:
            raise PermissionDeniedError("Cannot add a member with owner role")
        if member_role == PlaceRole.ADMIN and role != PlaceRole.VIEWER:
            raise PermissionDeniedError("Admin can only add viewers")
        if member_role not in (PlaceRole.OWNER, PlaceRole.ADMIN):
            raise PermissionDeniedError("Only owner or admin can add members")
        existing = await self.uow.place_member_repository.get_one_or_none(
            place_id=place_id, user_id=target_user_id
        )
        if existing:
            raise AlreadyExistsError("User is already a member of this place")
        await self.uow.place_member_repository.create(
            place_id=place_id, user_id=target_user_id, role=role
        )
        await self._publish_event(
            {
                "event_type": "member.added",
                "place_id": str(place_id),
                "user_id": str(target_user_id),
                "role": role.value,
            },
            key=f"{place_id}:{target_user_id}",
        )
        return True

    async def remove_member(self, user_id: UUID, place_id: UUID, target_user_id: UUID) -> bool:
        member_role = await self._get_member_or_fail(user_id, place_id)
        if member_role not in (PlaceRole.OWNER, PlaceRole.ADMIN):
            raise PermissionDeniedError("Only owner or admin can remove members")
        target = await self.uow.place_member_repository.get_one_or_none(
            place_id=place_id, user_id=target_user_id
        )
        if not target:
            raise NotFoundError("Target user is not a member of this place")
        if target.role == PlaceRole.OWNER:
            raise PermissionDeniedError("Cannot remove the owner")
        if member_role == PlaceRole.ADMIN and target.role != PlaceRole.VIEWER:
            raise PermissionDeniedError("Admin can only remove viewers")
        await self.uow.place_member_repository.delete(target)
        await self.broker.publish(
            None, topic=PLACES_EVENTS_TOPIC, key=f"{place_id}:{target_user_id}".encode()
        )
        return True

    async def update_member_role(
        self, user_id: UUID, place_id: UUID, target_user_id: UUID, role: PlaceRole
    ) -> bool:
        member_role = await self._get_member_or_fail(user_id, place_id)
        if member_role != PlaceRole.OWNER:
            raise PermissionDeniedError("Only owner can update member roles")
        if role == PlaceRole.OWNER:
            raise PermissionDeniedError("Cannot assign owner role")
        target = await self.uow.place_member_repository.get_one_or_none(
            place_id=place_id, user_id=target_user_id
        )
        if not target:
            raise NotFoundError("Target user is not a member of this place")
        if target.role == PlaceRole.OWNER:
            raise PermissionDeniedError("Cannot change the owner's role")
        await self.uow.place_member_repository.update(target.id, role=role)
        await self._publish_event(
            {
                "event_type": "member.role_changed",
                "place_id": str(place_id),
                "user_id": str(target_user_id),
                "role": role.value,
            },
            key=f"{place_id}:{target_user_id}",
        )
        return True

    async def list_members(self, user_id: UUID, place_id: UUID) -> list[PlaceMemberDTO]:
        await self._get_member_or_fail(user_id, place_id)
        members = await self.uow.place_member_repository.get_all(place_id=place_id)
        return [PlaceMemberDTO(user_id=m.user_id, role=m.role) for m in members]
