# Places Service

- **Port:** 50052
- **DB:** places_db (PostgreSQL)
- No dependencies on other gRPC services (called by others)

## Structure

```
src/
├── main.py                          # gRPC server, DI container (Dishka)
├── core/
│   ├── config.py                    # Pydantic Settings
│   ├── dto.py                       # PlaceDTO, PlaceMemberDTO, PlaceWithRoleDTO
│   ├── exceptions.py                # NotFoundError, AlreadyExistsError, PermissionDeniedError
│   └── types.py                     # IDType, UNSET sentinel
├── dependencies/
│   ├── config.py                    # Settings (APP scope)
│   ├── db.py                        # DatabaseHelper (APP), UoW (REQUEST, yield-based)
│   └── places.py                    # PlacesService (REQUEST)
├── handlers/
│   └── places.py                    # gRPC PlacesHandler
├── services/
│   └── places.py                    # CRUD places + member management
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
