# Places Service

- **Port:** 50052
- **DB:** places_db (PostgreSQL)
- **Kafka:** producer — publishes member/place events to `places.events` topic
- No dependencies on other gRPC services (called by others)

## Structure

```
src/
├── main.py                          # gRPC server + Kafka broker, DI container (Dishka)
├── core/
│   ├── config.py                    # Pydantic Settings
│   ├── dto.py                       # PlaceDTO, PlaceMemberDTO, PlaceWithRoleDTO
│   ├── exceptions.py                # NotFoundError, AlreadyExistsError, PermissionDeniedError
│   └── types.py                     # IDType, UNSET sentinel
├── dependencies/
│   ├── config.py                    # Settings (APP scope)
│   ├── db.py                        # DatabaseHelper (APP), UoW (REQUEST, yield-based)
│   ├── kafka.py                     # KafkaBroker (APP scope)
│   └── places.py                    # PlacesService (REQUEST)
├── handlers/
│   └── places.py                    # gRPC PlacesHandler
├── services/
│   └── places.py                    # CRUD places + member management + event publishing
└── infra/db/
    ├── helper.py                    # SQLAlchemy async engine + session factory
    ├── uow.py                       # UnitOfWork (AsyncContextManager)
    ├── models/                      # Place, PlaceMember (with PlaceRole enum)
    └── repositories/                # BaseRepository[T], PlaceRepository, PlaceMemberRepository
```

## Roles

- OWNER, ADMIN, VIEWER (PlaceRole StrEnum in models)
- Proto mapping via named constants `ROLE_OWNER`, `ROLE_ADMIN`, `ROLE_VIEWER` from `placebrain_contracts`

## Protobuf Imports

```python
from placebrain_contracts import places_pb2 as places_pb
from placebrain_contracts.places_pb2 import ROLE_OWNER, ROLE_ADMIN, ROLE_VIEWER
```

## Error Handling

Typed exceptions from `core/exceptions.py`:

| Exception             | gRPC StatusCode      |
|-----------------------|----------------------|
| `NotFoundError`       | `NOT_FOUND`          |
| `AlreadyExistsError`  | `ALREADY_EXISTS`     |
| `PermissionDeniedError` | `PERMISSION_DENIED` |

## UnitOfWork

Managed via DI teardown (yield-based). Services work with repositories directly without `async with self.uow:`.

## DTO

Services return DTOs from `core/dto.py`, not ORM models.

## Kafka Events (Producer)

Topic: `places.events`. All events use Pydantic models from `placebrain_contracts.events`.

| Action | Event Model | Consumers |
|--------|-------------|-----------|
| Create place (auto-add owner) | `MemberAdded` | devices |
| Add member | `MemberAdded` | devices |
| Remove member | `MemberRemoved` | devices |
| Change member role | `MemberRoleChanged` | devices |
| Delete place | `PlaceDeleted` | devices |

Publishing via `PlacesService._publish_event(event: BaseEvent, key: str)`.

**StrEnum → Literal:** `PlaceRole.value` returns `str`, but event models expect `Literal[...]`. Use `# type: ignore[arg-type]` on these lines — values are guaranteed to match.
