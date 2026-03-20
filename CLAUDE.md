# Places Service

- **Порт:** 50052
- **БД:** places_db (PostgreSQL)

## Роли

- OWNER (1), ADMIN (2), VIEWER (3)
- OWNER/ADMIN — write-операции, любой member — read

## RPC-методы

- CRUD places + member management
- Нет зависимостей от других gRPC-сервисов (вызывается другими)
- `PermissionError` → `PERMISSION_DENIED`, `ValueError` → `NOT_FOUND`/`ALREADY_EXISTS`
