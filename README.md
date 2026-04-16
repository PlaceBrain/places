# places

> gRPC service for managing places (locations) and their members in PlaceBrain.

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)
![gRPC](https://img.shields.io/badge/gRPC-1.76-green.svg)
![Kafka](https://img.shields.io/badge/Kafka-4.0-black.svg)

A "place" is the top-level tenant in PlaceBrain — a building, a warehouse, an office floor. This service owns places, their members, and the role of each member (`OWNER`, `ADMIN`, `VIEWER`). Every mutation becomes a Kafka event so the rest of the platform can react without synchronous RPC calls.

## Role in PlaceBrain

PlaceBrain is an open-source IoT platform for smart buildings. See the [organization profile](https://github.com/PlaceBrain) for the full architecture.

- Called over gRPC by the [gateway](https://github.com/PlaceBrain/gateway) for CRUD on places and members.
- Does **not** call any other PlaceBrain service.
- Publishes member/place lifecycle events to Kafka; the [devices](https://github.com/PlaceBrain/devices) service reacts to them (role cache invalidation, cascading device deletion via publisher chain).

## Tech stack

- Python 3.14, uv
- gRPC + [FastStream](https://faststream.airt.ai/) on aiokafka, with `dishka-faststream` for DI in subscribers
- Dishka DI (`APP` / `REQUEST` scopes)
- SQLAlchemy 2.0 async + asyncpg, Alembic migrations
- Pydantic Settings

## gRPC methods (port 50052)

| Method | Purpose |
|---|---|
| `CreatePlace` / `GetPlace` / `ListPlaces` / `UpdatePlace` / `DeletePlace` | Place CRUD |
| `AddMember` / `RemoveMember` / `ChangeMemberRole` / `GetMembers` | Membership management |

Proto definitions live in [placebrain-contracts](https://github.com/PlaceBrain/contracts) (`places.proto`).

## Kafka events (producer)

One topic per event type. Events are Pydantic models from `placebrain_contracts.events`; FastStream auto-serializes. Topic constants in `placebrain_contracts.events.topics`.

| Topic | Event | Triggered on |
|---|---|---|
| `places.member.added` | `MemberAdded` | `AddMember` |
| `places.member.removed` | `MemberRemoved` | `RemoveMember` |
| `places.member.role-changed` | `MemberRoleChanged` | `ChangeMemberRole` |
| `places.place.deleted` | `PlaceDeleted` | `DeletePlace` (devices consumes and publisher-chains `DevicesBulkDeleted`) |

All compacted with `cleanup.policy=compact` so new subscribers can recover the current state.

## Local development

**Full stack (recommended):** clone [infra](https://github.com/PlaceBrain/infra) and run `make dev`.

**Service-only mode:**

```bash
uv sync
cp .env.example .env          # set DATABASE__URL, KAFKA__URL
uv run alembic upgrade head
uv run python -m src
```

Requires a reachable PostgreSQL (`places_db`) and Kafka broker.

## Environment variables

All keys use `__` as nested delimiter. See [`.env.example`](./.env.example).

| Variable | Purpose |
|---|---|
| `DATABASE__URL` | `postgresql+asyncpg://...` DSN for `places_db` |
| `KAFKA__URL` | bootstrap server, e.g. `placebrain-kafka:19092` |

## Project layout

```
src/
├── main.py                  gRPC server + Kafka broker + DI
├── core/                    Settings, DTOs, typed exceptions
├── dependencies/            Dishka providers (config, db/uow, kafka, places)
├── handlers/places.py       gRPC PlacesHandler
├── services/places.py       Business logic + event publishing
└── infra/db/                SQLAlchemy models (Place, PlaceMember with PlaceRole enum), repositories, UoW
```

## Error model

| Exception | gRPC StatusCode |
|---|---|
| `NotFoundError` | `NOT_FOUND` |
| `AlreadyExistsError` | `ALREADY_EXISTS` |
| `PermissionDeniedError` | `PERMISSION_DENIED` |

## License

Apache License 2.0 — see [LICENSE](./LICENSE).
