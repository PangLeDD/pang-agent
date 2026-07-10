# Pang Agent Project Record

## Decisions

- Backend framework: FastAPI.
- Agent framework: LangGraph, deferred until the web and database foundation is stable.
- Database: PostgreSQL through SQLAlchemy async and `asyncpg`.
- Migrations: Alembic.
- Logging: Loguru.
- Auth: RBAC later. For now use a hardcoded development Bearer token stub.
- LLM provider: OpenAI-compatible chat API through LangChain `ChatOpenAI`; DeepSeek is only the current default endpoint/model.
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
- `app/agent/graph.py` owns the LangGraph invoke flow with LLM branch and echo fallback.
- `app/agent/llm.py` owns the OpenAI-compatible LLM client factory.
- `app/agent/prompt.py` owns the minimal system/user prompt builder.
- `app/agent/schema.py` owns Agent request/response DTOs.
- `app/core/exceptions.py` owns unified error responses: `{code, message, data}`.
- `app/core/response.py` owns unified success/error response payload helpers.
- `app/core/sse.py` formats SSE events with the same `{code, message, data}` envelope.
- `app/api/agent.py` exposes protected `POST /agent/invoke`.
- `POST /agent/invoke` returns a `conversation_id`; missing IDs are generated with UUID4 and not persisted yet.
- `POST /agent/stream` is the frontend-facing Agent message endpoint. SSE events use `meta`, `delta`, `done`, and `error`.
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
- `tests/test_agent_invoke.py` checks protected LangGraph invoke behavior.
- `tests/test_llm_client.py` checks missing LLM key behavior without making network calls.
- `tests/test_prompt.py` checks prompt assembly and LLM message invocation shape.
- `tests/test_exceptions.py` checks unified HTTP and validation error responses.

## Deferred

- RBAC models and real JWT login.
- Repository/service layers.
- Real database connectivity tests.
- Redis.
- Real LLM-backed LangGraph Agent behavior.
- Streaming LLM responses.
- Token-level LLM streaming; current SSE sends one delta per final reply.

## SSE Protocol

SSE events follow the `conversation.*` / `message.*` / `error` naming convention.
Each data payload is wrapped in an AgentEvent envelope: `{id, timestamp, payload}`.

The `{code, message, data}` structure is reserved for synchronous HTTP responses only.

```text
event: conversation.start
data: {"id":"evt_...","timestamp":1720000000000,"payload":{"conversation_id":"..."}}

event: message.delta
data: {"id":"evt_...","timestamp":1720000000000,"payload":{"delta":"..."}}

event: conversation.end
data: {"id":"evt_...","timestamp":1720000000000,"payload":{"reason":"stop"}}

event: error
data: {"id":"evt_...","timestamp":1720000000000,"payload":{"code":500,"message":"Internal Server Error"}}
```

Reserved for future:
- `agent.status` — Agent state transitions (planning, searching, executing)
- `agent.thought` — Chain-of-thought visibility
- `tool.call` / `tool.result` — Tool execution lifecycle

- RAG.
