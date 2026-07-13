# HANDOFF — 项目交接文档

> 写给一个完全没有上下文的新会话。读完就能接手。

## 项目目标

构建一个 AI Agent 应用——pang-agent。

- **后端**：FastAPI + LangGraph Agent + PostgreSQL + SQLAlchemy + Loguru
- **前端**：Vue3 + Vite + TypeScript，模仿 DeepSeek 聊天风格
- **长期**：RAG 增强检索、RBAC 认证鉴权、多 Agent 协作

当前阶段：**地基搭建完成，前后端联调通了 SSE 流式对话。**

---

## 已完成

### 后端

| 模块 | 状态 | 说明 |
|---|---|---|
| FastAPI 服务 | ✅ | `app/main.py` 入口，`create_app()` 工厂 |
| 配置 | ✅ | `app/config/config.py` pydantic-settings 单例，读 `.env` |
| API 路由 | ✅ | `public_router`（无需认证）/ `protected_router`（需 Bearer token） |
| LangGraph 图 | ✅ | 单节点 echo graph，LLM key 有 → 调 DeepSeek，无 → echo 回退 |
| SSE 流式 | ✅ | `POST /agent/stream`，使用 `sse-starlette` 的 `EventSourceResponse` |
| LLM 客户端 | ✅ | `app/infrastructure/llm/client.py`，OpenAI-compatible，默认 DeepSeek |
| 日志 | ✅ | Loguru，在 `create_app()` 中初始化 |
| 异常处理 | ✅ | 全局 handler，统一 `{code, message, data}` JSON |
| 认证桩 | ✅ | 开发用固定 Bearer token：`8d3f4bd6a70a4cb89c49f6a1b0f0d5d2` |
| LangSmith | ✅ | `app/config/__init__.py` 中 `apply_langsmith_env()` 设置环境变量 |
| 数据库 | ⚠️ | SQLAlchemy async engine + Base 就绪，Alembic 迁移已配置，但未实际建表 |

### 前端

| 模块 | 状态 | 说明 |
|---|---|---|
| 项目脚手架 | ✅ | Vue3 + Vite + TypeScript，`frontend/` |
| 聊天 UI | ✅ | 浅色主题，左侧栏 + 中间聊天 + 底部输入框 |
| SSE 连接 | ✅ | `useSSE.ts`，fetch POST + ReadableStream 手动解析 SSE |
| 打字机效果 | ✅ | `message.delta` 事件实时追加文字，闪烁光标 |
| Vite 代理 | ✅ | `/agent` → `http://localhost:8000` |

### 架构分层（按 `docs/ARCHITECTURE.md`）

```
app/api/            → 薄 HTTP 收口（只调 service，不写逻辑）
app/application/    → 编排一次请求（ChatService → AgentExecutor → SSE）
app/agent/          → Agent 运行时（graph / executor / events / prompt）
app/presentation/   → AgentEvent → 传输格式转换（当前 SSE）
app/infrastructure/ → 外部适配器（LLM 客户端）
app/core/           → 基础设施（DB、安全、异常、响应格式）
```

### 测试

- 21 个 `unittest` 用例，全部通过
- **测试用 `unittest`，不是 `pytest`**
- 运行：`uv run python -m unittest discover -s tests -v`

---

## SSE 协议

事件命名用点分格式，数据负载为 AgentEvent 信封：

```
event: conversation.start
data: {"id":"uuid","timestamp":1720000000000,"payload":{"conversation_id":"abc123"}}

event: message.delta
data: {"id":"uuid","timestamp":1720000000000,"payload":{"delta":"你"}}

event: conversation.end
data: {"id":"uuid","timestamp":1720000000000,"payload":{"reason":"stop"}}

event: error
data: {"id":"uuid","timestamp":1720000000000,"payload":{"code":500,"message":"Internal Server Error"}}
```

- `{code, message, data}` 格式**仅用于 HTTP 同步接口**，SSE 不用
- 事件类型常量定义在 `app/agent/events.py` 的 `EventType` 类中
- 预留事件类型：`agent.status`、`agent.thought`、`tool.call`、`tool.result`

---

## 当前进度和卡点

**进度**：地基打完，前后端 SSE 流式对话跑通。LLM key 配置后可真实调用 DeepSeek 并逐 token 流式返回。

**卡点**：无阻塞问题。项目处于可以继续往上盖功能的状态。

---

## 下一步计划

按优先级：

1. **会话持久化**——当前 conversation_id 不落库，重启丢失
2. **真实 Token 流式**——目前 echo_node 返回完整回复，然后 LangGraph 用 `stream_mode="messages"` 逐 token 吐出。后续应在 LLM 调用层直接流式
3. **前端左侧栏**——目前是"暂无历史会话"占位，需对接会话列表 API
4. **RBAC**——当前是 dev token 桩，需建 user/role/permission 表
5. **RAG**——预留，初版暂不考虑

---

## 踩过的坑（绝对不要再踩）

### 1. EventSourceResponse 的行分隔符

`sse-starlette` 的 `EventSourceResponse` 使用 `\r\n` 行尾，`\r\n\r\n` 分隔事件。前端解析时必须**先归一化 `\r\n` → `\n`** 再 `split('\n\n')`。

```typescript
// ❌ 错误：\r\n\r\n 里没有 \n\n，切不开
const parts = buffer.split('\n\n')

// ✅ 正确
const normalised = buffer.replace(/\r\n/g, '\n')
const parts = normalised.split('\n\n')
```

### 2. LangGraph 的 stream_mode

`agent_graph.astream()` 默认 `stream_mode="updates"`——等节点跑完才出完整结果。要实现逐 token 流式，必须用 `stream_mode="messages"`：

```python
# ❌ 整段一起出
async for chunk in agent_graph.astream({"message": msg, "reply": ""})

# ✅ 逐 token 出
async for chunk_msg, metadata in agent_graph.astream(
    {"message": msg, "reply": ""}, stream_mode="messages"
)
```

### 3. apply_langsmith_env 的调用时机

必须在**所有 LangChain import 之前**调用。我们放在 `app/config/__init__.py` 中：

```python
from .config import settings
settings.apply_langsmith_env()  # ← 必须最前面
```

### 4. 测试用的是 unittest

不是 pytest。没有 conftest。运行方式：

```bash
uv run python -m unittest discover -s tests -v
```

### 5. Alembic URL 需要驱动替换

Alembic 同步运行，需要把 `postgresql+asyncpg://` 替换为 `postgresql://`：

```python
def migration_url() -> str:
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
```

### 6. sse-starlette 的 data 字段

`EventSourceResponse` 的 `data` 字段**必须是预序列化的 JSON 字符串**，不能传 dict（会被当作 Python repr 而非 JSON）：

```python
# ❌ EventSourceResponse 会把 dict 当 repr 输出
return {"event": "x", "data": {"id": "1", "payload": ...}}

# ✅ 预先 json.dumps
return {"event": "x", "data": json.dumps({"id": "1", "payload": ...})}
```

### 7. 包 import 规范

- 跨包引用走 `__init__.py` 包级路径：`from app.agent import AgentExecutor`
- 同包内部可以直接引用模块：`from app.agent.graph import agent_graph`
- 单例在定义处实例化，不要在其他地方 `ClassName()`

### 8. 前端 ChatMain.vue 的 fallback 逻辑

`handleSend` 结束后有个 fallback：如果 `onEnd` 没触发但 `currentAssistantContent` 有值，仍然入消息列表。**不要删这个 fallback**——`onEnd` 在某些异常路径下可能不会被调用。

---

## 常用命令

```bash
# 后端
uv sync                          # 安装依赖
uv run uvicorn app.main:app --reload  # 启动后端
uv run python -m unittest discover -s tests -v  # 跑测试

# 数据库迁移
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head

# 前端
cd frontend
npm install
npm run dev                      # 启动前端开发服务器
npx vue-tsc --noEmit             # TypeScript 检查
npx vite build                   # 生产构建
```

## 环境变量参考（.env.example）

```
APP_NAME=pang-agent
LLM_API_KEY=          # 你的 DeepSeek key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LANGSMITH_API_KEY=    # LangSmith key
```

---

## 文件索引

| 文件 | 用途 |
|---|---|
| `docs/ARCHITECTURE.md` | 架构规范和编码规范 |
| `docs/PROJECT_RECORD.md` | 项目决策记录 |
| `app/main.py` | 应用入口 |
| `app/config/config.py` | 配置单例 |
| `app/config/__init__.py` | LangSmith 初始化 |
| `app/api/agent.py` | Agent API 端点 |
| `app/api/router.py` | 路由注册（public/protected） |
| `app/agent/graph.py` | LangGraph 图定义 |
| `app/agent/executor.py` | Agent 运行时 |
| `app/agent/events.py` | AgentEvent + EventType |
| `app/application/chat_service.py` | 对话编排 + DI |
| `app/presentation/sse.py` | SSE 信封格式化 |
| `app/infrastructure/llm/client.py` | LLM 客户端 |
| `app/core/security.py` | 认证桩（DEV_AUTH_TOKEN） |
| `frontend/src/components/ChatMain.vue` | 聊天主界面 |
| `frontend/src/composables/useSSE.ts` | SSE 连接逻辑 |
