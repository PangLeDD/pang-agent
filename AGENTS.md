# AGENTS.md — pang-agent

## 环境

- **Python 3.13**，包管理器 **uv**（`pyproject.toml` + `uv.lock`）
- 虚拟环境：`.venv/`，用 `uv run` 执行一切命令
- 环境变量：从 `.env` 读取（`.env.example` 是模板），`.env` 已被 gitignore
- OpenCode 配置：`opencode.json` 加载了 ponytail 和 superpowers 插件
- CodeGraph 索引存在于 `.codegraph/`，可用于 `codegraph_explore`

## 常用命令

```bash
# 安装/同步依赖
uv sync

# 运行全部测试（unittest，不是 pytest！）
uv run python -m unittest discover -s tests -v

# 运行单个测试文件
uv run python -m unittest tests.test_health -v

# 运行单个测试方法
uv run python -m unittest tests.test_health.HealthTest.test_health -v

# 生成 Alembic 迁移（autogenerate）
uv run alembic revision --autogenerate -m "描述"

# 应用迁移
uv run alembic upgrade head

# 启动开发服务器
uv run uvicorn app.main:app --reload
```

## 架构

分层设计：API → Application → Agent → Infrastructure，类似 Java MVC 但适配 Agent 场景。详细规范见 `docs/ARCHITECTURE.md`。

```
pang-agent/
├── app/
│   ├── main.py                  # FastAPI 入口，暴露 create_app() 和 app
│   ├── config/config.py          # pydantic-settings 配置单例 settings
│   ├── dependencies.py           # 全局依赖注入（当前为空）
│   ├── api/                      # 🌐 API 层：薄 HTTP 收口，只做协议转换
│   │   ├── router.py             # public_router + protected_router
│   │   ├── health.py             # GET /health
│   │   ├── agent.py              # POST /agent/invoke, /stream, /llm-test
│   │   └── users.py              # GET /users/me
│   ├── application/              # 📦 Application 层：编排一次请求的完整流程
│   │   └── chat_service.py       # ChatService → AgentExecutor → SSE
│   ├── agent/                    # 🧠 Agent/Domain 层：图运行、事件模型、prompt
│   │   ├── graph.py              # LangGraph 图定义 + invoke_agent()
│   │   ├── executor.py           # AgentExecutor：跑图，产出 AgentEvent 流
│   │   ├── events.py             # AgentEvent 领域模型（LLM 和业务之间的防腐层）
│   │   ├── prompt.py             # system/user prompt 构建
│   │   ├── state.py              # AgentState TypedDict
│   │   └── schema.py             # Agent DTO（请求/响应）
│   ├── presentation/             # 🎨 Presentation 层：AgentEvent → 传输格式
│   │   └── sse.py                # SSE 事件格式化
│   ├── infrastructure/           # 🏗️ Infrastructure 层：外部系统适配器
│   │   └── llm/
│   │       └── client.py         # OpenAI-compatible LLM 客户端
│   ├── core/                     # 🧱 核心基础设施
│   │   ├── database.py           # SQLAlchemy async engine + session + Base
│   │   ├── security.py           # 开发用 Bearer token 认证桩
│   │   ├── exceptions.py         # 全局异常处理 → 统一 JSON
│   │   ├── response.py           # success() / error_payload()
│   │   └── logging.py            # Loguru 初始化
│   ├── models/                   # SQLAlchemy ORM 模型（user.py 为空占位）
│   ├── schemas/                  # Pydantic 校验模型（部分为空占位）
│   ├── services/                 # 业务逻辑层（待迁移到 application/）
│   └── repositories/             # 数据访问层（base_repo.py 为空占位）
├── tests/                        # unittest 测试，21 个用例全部通过
├── alembic/                      # 数据库迁移（env.py + versions/）
├── frontend/                     # 前端（当前为空）
└── docs/PROJECT_RECORD.md        # 项目决策记录
```

## 关键约定

### 测试
- **使用 `unittest`，不是 `pytest`**。没有 conftest.py，没有 fixture。
- 测试文件命名：`tests/test_*.py`
- 运行：`uv run python -m unittest discover -s tests -v`
- **开发期间不主动写 unittest**：除非用户明确要求写测试，否则只实现功能代码，接口由用户自行测试验证。

### API 响应格式
所有响应统一为 `{code: int, message: str, data: Any}`。必须使用 `app.core.response.success()` / `app.core.response.error_payload()` 构建，禁止手写结构。

### 认证
- 当前是开发桩：`Bearer <DEV_AUTH_TOKEN>`（token 值见 `app/core/security.py`）
- 需要认证的路由挂到 `protected_router`，公开路由挂到 `public_router`
- 新增 API 时显式选择挂载到哪个 router

### SSE 协议
SSE 事件使用 `conversation.start` / `message.delta` / `conversation.end` / `error` 四种 event name。数据负载为 AgentEvent 信封 `{id, timestamp, payload}`。格式定义见 `docs/PROJECT_RECORD.md`。

注意：`{code, message, data}` 只在 HTTP 同步接口使用，SSE 不用这个格式。

### Alembic
- `alembic/env.py` 自动从 `settings.database_url` 读取连接串
- **关键**：Alembic 同步运行，需要把 `postgresql+asyncpg://` 替换为 `postgresql://`（已在 `migration_url()` 中处理）
- 迁移目标 metadata = `app.core.database.Base.metadata`

### LLM
- LLM key 可选：没有 key 时 LangGraph 进入 echo 回退模式（返回 `pang-agent received: <消息>`）
- `invoke_llm()` 需要 key，没有 key 时抛 `RuntimeError`
- 测试中修改 `settings.llm_api_key` 后必须在 `finally` 中恢复

### 日志
- 使用 Loguru，初始化在 `create_app()` 中调用 `setup_logging()`
- 不要在 handler 中直接 `print()` 或用 `logging` 标准库

### 包索引
- PyPI 镜像设为清华源（`pyproject.toml` 中配置），不要在命令中加 `-i` 参数

## 占位/空文件

以下文件是有意留空的结构占位，不要删除：
- `app/dependencies.py`
- `app/models/user.py`
- `app/schemas/common.py`
- `app/schemas/user.py`
- `app/repositories/base_repo.py`
- `frontend/` 目录（保留目录结构）
