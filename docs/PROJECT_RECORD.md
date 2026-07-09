# Pang Agent Project Record

## Decisions

- Backend framework: FastAPI.
- Agent framework: LangGraph, deferred until the web and database foundation is stable.
- Database: PostgreSQL through SQLAlchemy async and `asyncpg`.
- Migrations: Alembic.
- Logging: Loguru.
- Auth: RBAC later. For now use a hardcoded development Bearer token stub.
- RAG: reserved for a later slice.

## Current Foundation

- `app/main.py` exposes `create_app()` and `app`.
- `app/api/router.py` separates public and protected route groups; protected routes share the auth dependency.
- `app/api/health.py` exposes `GET /health`.
- `app/core/logging.py` configures Loguru at app creation.
- `app/config/config.py` owns environment-backed settings.
- `app/core/database.py` owns SQLAlchemy `Base`, async engine, async session factory, and session dependency.
- `app/core/security.py` owns the temporary Bearer token authentication stub.
- `app/api/users.py` exposes `GET /users/me` as the protected smoke endpoint.
- `alembic/env.py` reads `settings.database_url` and `Base.metadata`.

## Environment

`.env` is local and ignored by git. `.env.example` is the template.

Current default database URL:

```text
postgresql+asyncpg://postgres:postgres@192.168.1.51:5432/pang_agent
```

API keys stay empty in templates and local `.env` until manually filled.

## Tests

- `tests/test_health.py` checks `GET /health`.
- `tests/test_database.py` checks database foundation imports without connecting to PostgreSQL.
- `tests/test_auth_stub.py` checks missing, wrong, and correct Bearer token behavior.

## Deferred

- RBAC models and real JWT login.
- Repository/service layers.
- Real database connectivity tests.
- Redis.
- LangGraph Agent endpoints.
- RAG.
