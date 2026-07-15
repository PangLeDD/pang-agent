很多人的项目一开始只有一个 graph：

```text
chat_graph.py
```

后来越来越多：

```text
chat_graph.py
agent_graph.py
workflow_graph.py
summary_graph.py
planning_graph.py
tool_graph.py
review_graph.py
...
```

最后：

```python
if type == "chat":
    graph = create_chat_graph()

elif type == "summary":
    graph = create_summary_graph()

elif ...
```

整个项目就炸了。

---

# 我建议你先建立一个思想：

> **Graph 不是 Service。**

很多人把：

```text
ChatService
    │
    ▼
create_graph()
```

写在一起。

其实 Graph 更像：

> **Spring 中的 Bean 配置。**

它负责：

```text
Node

↓

Edge

↓

Compile

↓

CompiledGraph
```

它不是业务逻辑。

---

# 我一般会拆成四层

```
api
│
application
│
agent
│
infrastructure
```

其中：

```
agent
│
├── nodes
├── graphs
├── registry
├── builder
└── state
```

这是 Agent 自己就是一个领域。

---

## 第一层：nodes（最稳定）

例如：

```
agent
│
└── nodes
    ├── llm_node.py
    ├── tool_node.py
    ├── planner_node.py
    ├── memory_node.py
    └── summary_node.py
```

例如：

```python
class LLMNode:

    async def __call__(state):

        ...
```

或者：

```python
async def llm_node(state):
```

一个文件一个 Node。

Node 不知道 Graph。

---

## 第二层：state

例如：

```
state

├── chat_state.py
├── planning_state.py
└── summary_state.py
```

例如：

```python
class ChatState(TypedDict):

    messages: list

    user_id: str

    context: dict
```

每个 Graph 可以有自己的 State。

---

## 第三层：builder（⭐⭐⭐⭐⭐）

这是很多项目没有的。

例如：

```
builder

├── chat_builder.py
├── planning_builder.py
└── review_builder.py
```

例如：

```python
class ChatGraphBuilder:

    def build(

        self,

        llm,

        memory,

        checkpoint,

    ):

        graph = StateGraph(ChatState)

        graph.add_node(...)

        graph.add_edge(...)

        ...

        return graph.compile(...)
```

这里只有：

> **组装。**

没有业务。

---

## 第四层：registry

例如：

```
registry

graph_registry.py
```

例如：

```python
class GraphRegistry:

    def __init__(self):

        self._graphs={}
```

注册：

```python
registry.register(
    "chat",
    ChatGraphBuilder()
)
```

获取：

```python
builder = registry.get("chat")
```

以后：

```
chat

summary

review

planning
```

都不用：

```python
if...
```

---

# Factory 怎么配合？

例如：

```
GraphFactory
```

负责：

```python
class GraphFactory:

    def create(

        self,

        graph_name,

        llm,

        checkpoint,

    ):

        builder = registry.get(
            graph_name
        )

        return builder.build(
            llm,
            checkpoint
        )
```

以后：

Service：

```python
graph = graph_factory.create(
    "chat"
)
```

不知道是谁。

---

# Graph 多了怎么办？

假设以后：

```
聊天

工作流

审批

RAG

Research

Coding

Review

Summary

Meeting
```

不要：

```
graphs

├── chat.py
├── coding.py
├── review.py
├── summary.py
...
```

我一般按业务拆。

例如：

```
agent

├── chat
│   ├── nodes
│   ├── builder.py
│   └── state.py
│
├── research
│   ├── nodes
│   ├── builder.py
│   └── state.py
│
├── workflow
│   ├── nodes
│   ├── builder.py
│   └── state.py
```

是不是舒服很多？

一个业务一个目录。

---

# 更大型怎么办？

很多 AI Agent 项目最后会这样：

```
agent

├── graph
│     builder.py
│
├── node
│
├── tool
│
├── prompt
│
├── state
│
├── middleware
│
└── runtime
```

GraphBuilder：

```python
builder.build()

↓

Node

↓

Prompt

↓

Middleware

↓

Compile
```

整个流程很清晰。

---

# 我自己的经验（也是我最推荐给你的）

结合你前面一直在问的内容（FastAPI、Container、生命周期、多 LLM、多用户配置），如果是我来设计，我会把 **Graph 看成一种"可配置资源"**，而不是业务代码。

整个项目会是这样的：

```text
app
│
├── api/
├── application/
│   └── chat_service.py
│
├── agent/
│   ├── chat/
│   │   ├── builder.py
│   │   ├── state.py
│   │   └── nodes/
│   ├── research/
│   │   ├── builder.py
│   │   ├── state.py
│   │   └── nodes/
│   ├── registry.py
│   └── factory.py
│
├── infrastructure/
│
└── container.py
```

然后：

* **Node**：最小业务单元，可复用。
* **Builder**：负责组装一个 Graph。
* **Registry**：负责登记有哪些 Graph。
* **Factory**：根据配置、用户类型或业务场景选择 Builder 并编译（或返回缓存的 CompiledGraph）。
* **Service**：只负责调用 Graph，不关心 Graph 是怎么拼出来的。

---

## 最后给你一个我觉得特别重要的建议

我发现你现在已经开始思考**架构层面**的问题了，而不是"代码放哪"的问题。

接下来你可以逐渐建立一种类似 Spring 的分层思维，但不要照搬 Spring。

在 AI Agent 项目里，我通常会把系统分成五个角色，每个角色只有一种职责：

| 角色            | 职责                                     |
| ------------- | -------------------------------------- |
| **Container** | 管理生命周期长的共享资源（DB、Redis、Factory 等）       |
| **Factory**   | 根据配置创建动态对象（LLM、Graph、Memory 等）         |
| **Builder**   | 负责"组装"，例如拼装 LangGraph、Workflow、Tool 集合 |
| **Service**   | 编排业务流程，调用 Graph、Repository、外部服务        |
| **Node**      | 完成单一 AI 能力或业务动作，尽量保持可复用                |

如果始终坚持这几个角色各司其职，即使以后从 1 个 Graph 增长到 30 个 Graph，维护成本也不会线性增长，代码的可读性和扩展性都会好很多。
