你的理解其实是比较接近**传统 Java 企业开发分层思想**的：

```
Controller
    |
Service
    |
Repository
```

Controller 只负责：

* 接收请求
* 参数校验
* 调用 Service
* 返回结果

业务逻辑全部下沉。

这个思想在 FastAPI 里依然成立，但是 **AI Agent 项目会稍微变化**，因为 Agent 本身不是普通业务逻辑，它更像一个「动态流程引擎」。

所以 FastAPI + Agent 项目通常会演化成：

```
API层
  |
  | 负责 HTTP / SSE 协议
  |
Application层
  |
  | 编排一次请求的流程
  |
Domain / Agent层
  |
  | Agent推理、工具调用、记忆、规划
  |
Infrastructure层
  |
  | DB、VectorDB、LLM、第三方API
```

---

## 先回答你的核心问题：

> 返回前端数据以及大模型返回数据中间的数据转换代码放哪里？

不要放 API 层。

比如：

你的接口：

```python
POST /chat
```

收到：

```json
{
 "message":"帮我分析销售数据"
}
```

LLM 返回：

```python
AIMessage(
 content="分析结果..."
 tool_calls=[
   ...
 ]
)
```

然后你需要转换成：

```json
{
 "type":"message.delta",
 "data":{
    "content":"分析结果"
 }
}
```

这个转换逻辑**不属于 API 层**。

---

# 推荐结构

例如：

```
app
│
├── api
│   └── chat.py
│
├── application
│   └── chat_service.py
│
├── agent
│   ├── executor.py
│   ├── planner.py
│   └── memory.py
│
├── schemas
│   └── event.py
│
├── infrastructure
│   ├── llm
│   └── database
│
└── core
```

---

## API层

非常薄：

```python
@router.post("/chat")
async def chat(
    request: ChatRequest
):

    return StreamingResponse(
        chat_service.stream(
            request
        ),
        media_type="text/event-stream"
    )
```

结束。

这里甚至不应该出现：

```python
if tool_call:
    xxx

if message:
    xxx

if llm:
    xxx
```

---

# Application Service

这里类似 Java Service。

比如：

```python
class ChatService:


    async def stream(
        self,
        request
    ):

        async for event in agent.run(request):

            yield event_transformer.to_sse(event)

```

它负责：

一次用户请求的完整流程。

类似：

Java：

```java
OrderService.createOrder()
```

这里：

```python
ChatService.chat()
```

---

# Agent层

这里是 AI 项目特殊地方。

例如：

```
agent
 |
 ├── planner
 |
 ├── executor
 |
 ├── tool_manager
 |
 └── memory_manager

```

例如：

```python
class AgentExecutor:


    async def run(self, input):

        plan = await planner.create_plan()

        result = await execute(plan)

        yield AgentEvent(
            type="message.delta"
        )
```

这里产生：

```
AgentEvent
```

---

# 那数据转换放哪里？

我建议单独一层：

```
schemas
   |
   └── transformer
```

例如：

LLM 原始结果：

```python
AIMessage(
 content="hello"
)
```

转换：

```python
class AgentEventMapper:


    def message_to_event(
        self,
        message
    ):

        return AgentEvent(
            type="message.delta",
            data={
                "content":message.content
            }
        )

```

---

然后：

```
LLM
 |
 |
AgentMessage
 |
 |
Mapper
 |
 |
AgentEvent
 |
 |
SSE Formatter
 |
 |
Frontend
```

---

# 为什么不要直接在 Service 转？

很多人第一版会这样：

```python
async def chat():

    result = llm.invoke()

    return {
      "type":"message",
      "content":result.content
    }

```

看起来简单。

但是半年后：

需求：

### 增加微信端

需要：

```json
{
"type":"wx_message"
}
```

### 增加Web端

需要：

```json
{
"type":"sse_event"
}
```

### 增加语音端

需要：

```json
{
"type":"audio_chunk"
}
```

然后 Service 变成：

```python
if client=="web":
   xxx

elif client=="wx":
   xxx

elif client=="voice":
   xxx
```

污染业务。

---

# AI Agent 项目一个非常重要的概念

不要把：

```
LLM返回
```

直接当成：

```
业务返回
```

中间应该有一个自己的领域模型。

例如：

LLM：

```
OpenAIMessage
LangchainMessage
ClaudeMessage
```

你的系统：

```
AgentEvent
```

前端：

```
SSE Event
```

三层：

```
        OpenAI
          |
          |
    LLM Adapter
          |
          ↓
     AgentEvent
          |
          |
    Presentation Mapper
          |
          ↓
        SSE
```

这样以后换模型：

GPT
Claude
Gemini

都不会影响前端。

---

# 如果类比 Java

传统：

```
Controller

↓

Service

↓

DAO
```

AI Agent：

```
FastAPI Router

↓

Application Service

↓

Agent Runtime

↓

LLM Adapter

↓

Model Provider
```

多了一层：

```
Agent Runtime
```

因为 Agent 本身就是业务。

---

# 一个比较成熟的目录大概这样

```
backend

├── api
│   └── chat.py             # HTTP入口
│
├── application
│   └── chat_service.py     # 用例编排
│
├── domain
│   ├── agent.py            # Agent核心
│   ├── events.py           # Agent事件模型
│   └── memory.py
│
├── infrastructure
│   ├── llm
│   │    └── openai.py
│   ├── vector
│   └── db
│
├── presentation
│   └── sse_mapper.py       # 给前端的数据格式
│
└── schemas
    ├── request.py
    └── response.py
```

---

所以你的 Java 思维不用丢：

> **API 层薄，Service 层编排，业务下沉。**

只是到了 Agent：

> **Service 不直接处理 LLM，而是调用 Agent Runtime；LLM 返回也不要直接给前端，中间要有自己的 Event 模型。**

你之前研究 Agent Memory、Planner 那套，其实已经接近这个架构了。真正做平台级 Agent 时，**AgentEvent 这一层非常关键**，它就是连接「模型世界」和「业务系统世界」的防腐层。
