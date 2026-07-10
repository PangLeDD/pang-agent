# 项目架构规范

## 分层设计

```
┌─────────────────────────────────────────┐
│  API 层 (app/api/)                       │
│  薄 HTTP 收口：只做协议转换，不写业务     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Application 层 (app/application/)       │
│  编排一次请求的完整流程                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Domain / Agent 层 (app/agent/)          │
│  Agent 推理、图执行、事件模型             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Infrastructure 层 (app/infrastructure/) │
│  LLM、DB、外部 API 适配器                │
└─────────────────────────────────────────┘

         ┌──────────────┐
         │ Presentation │  ← 横切：AgentEvent → 传输格式
         └──────────────┘
```

## 各层职责

### API 层 (`app/api/`)

- **只做**：接收请求、参数校验、调用 Application Service、返回响应
- **不做**：业务判断、数据转换、LLM 调用、SSE 拼装
- **反例**：在路由函数里写 `if event.type == "message.delta": ...`

正确姿势：
```python
@router.post("/stream")
async def stream(request: AgentInvokeRequest) -> StreamingResponse:
    return StreamingResponse(
        chat_service.stream(request.message),
        media_type="text/event-stream",
    )
```

### Application 层 (`app/application/`)

- 类似 Java 的 Service 层，编排一次用户请求的**完整流程**
- 负责：调用 AgentExecutor、注入会话 ID、异常兜底、调用 Presentation 格式化
- **不做**：直接调 LLM、直接拼 SSE 字符串（交给 Presentation 层）

### Agent / Domain 层 (`app/agent/`)

- Agent 自身的"业务逻辑"：图定义、图执行、prompt 构建
- **核心概念**：`AgentEvent`——领域事件模型，连接「模型世界」和「业务系统」
- `AgentExecutor` 是本层唯一对外接口，外部不直接碰图

### Presentation 层 (`app/presentation/`)

- 负责输出格式转换：`AgentEvent → SSE / WebSocket / 语音 / ...`
- 当前只有 SSE，未来多端接入时只加新的 Mapper，不改业务代码

### Infrastructure 层 (`app/infrastructure/`)

- 外部系统适配器：LLM 客户端、数据库连接池、向量库等
- 隔离技术细节，Domain 层不直接依赖具体 SDK 实现

## AgentEvent — 防腐层

不要把 LLM 的原始返回（AIMessage、OpenAI chunk）直接抛给前端。中间必须有领域事件模型：

```
LLM 原始输出              AgentEvent              传输格式
─────────────            ───────────             ──────────
OpenAI chunk    ──►     AgentEvent       ──►     SSE 字符串
Claude stream           (type, payload)          WebSocket 帧
DeepSeek msg                                     语音 chunk
```

好处：
- 换模型（GPT→Claude→Gemini）不影响前端
- 多端接入（Web/微信/语音）不改 Agent 代码
- Agent 内部过程（思考/工具调用/规划）统一用一种事件描述

## 数据流（以 SSE Stream 为例）

```
POST /agent/stream
       │
       ▼
  api/agent.py         薄收口：return StreamingResponse(service.stream(...))
       │
       ▼
  application/chat_service.py   编排：跑 executor → 注入 cid → 转 SSE
       │
       ▼
  agent/executor.py            跑 graph.astream(stream_mode="messages")
       │                        产出 AgentEvent(type, payload)
       ▼
  agent/events.py              AgentEvent 领域模型
       │
       ▼
  presentation/sse.py          AgentEvent → SSE 字符串
```

## 目录结构

```
app/
├── api/                    # 🌐 API 层
│   ├── router.py
│   ├── health.py
│   ├── agent.py
│   └── users.py
├── application/            # 📦 Application 层
│   └── chat_service.py
├── agent/                  # 🧠 Agent/Domain 层
│   ├── graph.py            # LangGraph 图定义
│   ├── executor.py         # AgentExecutor 运行时
│   ├── events.py           # AgentEvent 领域模型
│   ├── prompt.py
│   ├── state.py
│   └── schema.py           # 请求/响应 DTO
├── presentation/           # 🎨 Presentation 层
│   └── sse.py              # SSE 格式化
├── infrastructure/         # 🏗️ Infrastructure 层
│   └── llm/
│       └── client.py       # LLM 客户端适配器
├── core/                   # 🧱 核心基础设施
│   ├── database.py
│   ├── security.py
│   ├── exceptions.py
│   ├── response.py
│   └── logging.py
├── models/                 # SQLAlchemy ORM
├── schemas/                # Pydantic 校验
├── services/               # 旧业务层（待迁）
└── repositories/           # 数据访问
```

## 编码规范

### 新增 API

1. 在 `app/api/` 建路由，继承 `router.py` 的 `public_router` 或 `protected_router`
2. 路由函数 ≤ 10 行——调用 Application Service，返回结果
3. 不要在里面调 graph、调 LLM、拼 SSE

### 新增 Agent 能力

1. 图节点加在 `app/agent/graph.py`
2. 如果图执行逻辑变复杂，在 `executor.py` 新增方法
3. 所有图输出先收敛为 `AgentEvent`，再交给上层

### 新增传输格式

1. 在 `app/presentation/` 新增文件
2. 实现 `AgentEvent → 目标格式` 的转换
3. 不改 Agent 层和 Application 层

### 新增外部依赖

1. 适配器放 `app/infrastructure/`
2. Domain 层通过接口（未来）或直接 import 适配器调用

## 包规范

### `__init__.py` 导出

每个包通过 `__init__.py` 公开其对外接口，调用方尽量用包级路径：

```python
# 推荐：包级 import
from app.agent import AgentExecutor, invoke_agent
from app.application import ChatService, get_chat_service
from app.presentation import sse_event
from app.infrastructure.llm import invoke_llm, get_llm

# 避免：深层模块 import（除非是同包内部避免循环引用）
from app.agent.graph import invoke_agent  # 同包内可以，跨包不推荐
```

跨包调用**必须**走包级 `__init__.py`；同包内部可以直接引用模块。

### 单例

单例对象在定义处就近实例化，不在调用方实例化：

```python
# chat_service.py — 定义和实例化在同一文件
class ChatService:
    ...

_chat_service = ChatService()  # ponytail: 模块级单例

def get_chat_service() -> ChatService:
    return _chat_service
```

### FastAPI 依赖注入

需要依赖注入时用 `Annotated[Type, Depends(provider)]` 风格：

```python
from typing import Annotated
from fastapi import Depends

@router.post("/stream")
async def stream(
    request: AgentInvokeRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> EventSourceResponse:
    return EventSourceResponse(service.stream(request.message))
```

依赖提供商函数（如 `get_chat_service`）放在对应类所在的模块中，保持就近原则。
