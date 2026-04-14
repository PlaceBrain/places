# Places Service

- **Порт:** 50052
- **БД:** places_db (PostgreSQL)
- Нет зависимостей от других gRPC-сервисов (вызывается другими)

## Структура

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
    ├── models/                      # Place, PlaceMember (с PlaceRole enum)
    └── repositories/                # BaseRepository[T], PlaceRepository, PlaceMemberRepository
```

## Роли

- OWNER, ADMIN, VIEWER (PlaceRole StrEnum в models)
- Proto-маппинг через именованные константы `ROLE_OWNER`, `ROLE_ADMIN`, `ROLE_VIEWER` из `placebrain_contracts`

## Protobuf-импорты

```python
from placebrain_contracts import places_pb2 as places_pb
from placebrain_contracts.places_pb2 import ROLE_OWNER, ROLE_ADMIN, ROLE_VIEWER
```

## Обработка ошибок

Типизированные исключения из `core/exceptions.py`:

| Exception             | gRPC StatusCode      |
|-----------------------|----------------------|
| `NotFoundError`       | `NOT_FOUND`          |
| `AlreadyExistsError`  | `ALREADY_EXISTS`     |
| `PermissionDeniedError` | `PERMISSION_DENIED` |

## UnitOfWork

Управляется через DI teardown (yield-based). Сервисы работают с репозиториями напрямую без `async with self.uow:`.

## DTO

Сервисы возвращают DTO из `core/dto.py`, не ORM-модели.
