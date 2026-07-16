很多人刚接触 LangGraph 会认为：

> **Checkpoint = 聊天记录**

实际上：

> **Checkpoint ≠ 聊天记录（Conversation History）**

企业项目一般都会把它们彻底分开。

---

# 我们先看看整个系统

一般会有三套"记忆"。

```text
                   AI Agent

                  State
                    │
                    │
      ┌─────────────┼─────────────┐
      │             │             │
      ▼             ▼             ▼

Checkpoint      Conversation      Long Memory
(恢复运行)       (聊天记录)       (用户事实)

PG               MySQL/PG          PG/Redis/VectorDB
```

三者职责完全不同。

---

# 第一种：Checkpoint

例如：

```python
messages
intent
tool_results
summary
```

它保存的是：

> **Graph 当前运行状态**

例如：

```text
NodeA
 ↓
NodeB
 ↓
NodeC
```

突然：

```
服务器重启
```

恢复：

```
Checkpoint

↓

NodeC继续跑
```

它不是给前端看的。

里面甚至会有：

```
ToolMessage

AIMessage(tool_calls)

metadata

usage
```

前端根本不关心这些。

---

# 第二种：Conversation（聊天记录）

这个就是前端左边栏。

例如：

```
今天
  AI项目讨论

昨天
  PostgreSQL同步

前天
  FastAPI认证
```

数据库一般设计成：

## conversation

```text
id

user_id

title

created_at

updated_at
```

例如：

| id | title        |
| -- | ------------ |
| 1  | AI Agent开发   |
| 2  | PostgreSQL同步 |

---

然后：

## conversation_message

```text
id

conversation_id

role

content

created_at
```

例如：

| role      | content |
| --------- | ------- |
| user      | 你好      |
| assistant | 你好      |
| user      | 帮我写代码   |

这里只保存：

```
role

content
```

不会保存：

```
tool_call

metadata

response_metadata

usage

id

artifact
```

因为没必要。

---

所以数据库其实长这样：

```text
conversation

1 AI Agent

↓

conversation_message

user

assistant

user

assistant
```

这就是前端历史聊天。

---

# 第三种：Memory

这个和聊天记录又不同。

例如：

聊天：

```
用户：

我叫张三
```

Memory Service 提取：

```
name=张三
```

聊天：

```
我喜欢Java
```

Memory：

```
favorite_language=Java
```

以后：

```
Hi 张三
```

不是去翻聊天记录。

而是：

```
Memory

↓

name=张三
```

速度快得多。

---

# 那 ChatGPT 左边栏是怎么来的？

其实就是：

```
Conversation
```

例如：

```
GET

/conversations
```

返回：

```json
[
 {
   "id":"1",
   "title":"AI Agent开发"
 },
 {
   "id":"2",
   "title":"FastAPI"
 }
]
```

点进去：

```
GET

/conversations/1/messages
```

返回：

```json
[
 {
   "role":"user",
   "content":"你好"
 },
 {
   "role":"assistant",
   "content":"你好"
 }
]
```

和 Checkpoint 一点关系都没有。

---

# 那 Checkpoint 和 Conversation 如何对应？

企业里通常会统一一个 **conversation_id（或 thread_id）**。

例如：

```text
conversation

id = conv001
```

Graph：

```python
config = {
    "configurable": {
        "thread_id": "conv001"
    }
}
```

于是：

```text
Conversation
       │
       │ id=conv001
       ▼

Checkpoint(thread_id=conv001)
```

所以：

```
conversation_id
==
thread_id
```

很多公司就是直接这么设计。

---

# 发送消息的时候流程

假设：

用户：

```
帮我查订单
```

整个流程：

```text
Frontend

        │
        ▼

POST /chat

        │
        ▼

保存用户消息
ConversationMessage

        │
        ▼

invoke Graph

thread_id=conv001

        │
        ▼

Graph

Checkpoint更新

        │
        ▼

AI回答

        │
        ▼

保存AI消息

ConversationMessage

        │
        ▼

返回前端
```

注意：

聊天记录和 Checkpoint 是**同时更新**，但**不是同一份数据**。

---

# 为什么不能直接把 Checkpoint 当聊天记录？

因为 Checkpoint 会越来越复杂。

例如：

```python
AIMessage(
    content="",
    tool_calls=[
      ...
    ]
)
```

还有：

```python
ToolMessage(...)
```

还有：

```python
RemoveMessage(...)
```

还有：

```python
usage_metadata
```

还有：

```python
response_metadata
```

还有：

```python
artifact
```

甚至：

```python
retrieved_docs
```

这些东西：

前端：

```
完全不需要。
```

如果直接展示：

```
ToolMessage：

调用工具：

xxxx
```

用户体验非常差。

所以：

企业都会再建：

```
conversation_message
```

专门给 UI。

---

# 那是不是维护两份数据？

没错。

企业基本都是：

```
Graph
     │
     ├────Checkpoint
     │
     └────Conversation
```

很多人第一反应是："这不是重复了吗？"

其实不是。

Checkpoint 是**运行时状态**。

Conversation 是**产品数据**。

就像：

```
Redis

MySQL
```

都会存一份。

职责完全不同。

---

# 我建议你未来项目直接采用这一套

结合我们之前讨论的 `FastAPI + LangGraph + Container`，一个比较清晰的架构可以是：

```text
                 Frontend
                      │
                      ▼
              ChatController(API)
                      │
                      ▼
               ChatApplication
                      │
      ┌───────────────┴────────────────┐
      │                                │
      ▼                                ▼
ConversationService             AgentService
(保存/查询聊天记录)             (调用 LangGraph)
      │                                │
      ▼                                ▼
conversation_message            Checkpointer
      │                                │
      └───────────────┬────────────────┘
                      ▼
                 返回 AI 回复
```

这样做有几个好处：

* **聊天记录**只关心产品展示（角色、内容、时间等）。
* **Checkpoint**只关心 Agent 的恢复和状态管理。
* 两者通过统一的 `conversation_id/thread_id` 关联，但彼此独立。
* 以后你要支持消息编辑、删除、重新生成、分享会话、导出聊天记录，都不会影响 LangGraph 的运行状态。

---

我还可以继续和你聊一个企业项目里经常会遇到的问题：

> **如果 Conversation 已经保存了全部聊天记录，而 Checkpoint 也保存了 `messages`，为什么很多公司在恢复一个会话时，仍然不会从 Conversation 重新构造 `messages`，而是优先恢复 Checkpoint？**

这个问题会涉及 **LangGraph Checkpoint 的增量状态恢复机制**，也是很多人在做生产环境时容易踩坑的地方。
