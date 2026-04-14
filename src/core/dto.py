from dataclasses import dataclass

from src.core.types import IDType
from src.infra.db.models.place_member import PlaceRole


@dataclass(frozen=True, slots=True)
class PlaceDTO:
    id: IDType
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class PlaceMemberDTO:
    user_id: IDType
    role: PlaceRole


@dataclass(frozen=True, slots=True)
class PlaceWithRoleDTO:
    id: IDType
    name: str
    description: str
    role: PlaceRole
