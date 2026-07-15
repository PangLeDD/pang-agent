# LangGraph State 设计笔记

## 一、State 是什么？

一句话：

> **State 是一次 Graph 执行过程中，所有 Node 共享的数据上下文。**

它不是数据库，不是资源容器，更不是业务 Service。

可以把它理解成医院里的**病历**：

``` text
病人
 ↓
医生（写一点）
 ↓
化验室（写一点）
 ↓
药房（写一点）
 ↓
病历越来越完整
```

每个 Node： - 读取 State - 修改 State - 返回 State

Node 之间不要直接调用，而是通过 State 交换数据。

------------------------------------------------------------------------

## 二、State 与 HTTP Request 的关系

很多人容易混淆两个概念：

``` text
HTTP Request
```

和

``` text
Conversation（聊天会话）
```

例如：

    Request1 -> "你好"
    Request2 -> "上海天气"
    Request3 -> "北京天气"

每一个 Request 都是新的。

但是：

    Conversation #123

    你好
    ↓

    上海天气

    ↓

    北京天气

属于同一个聊天。

所以：

-   Request 生命周期：一次请求结束即销毁
-   Conversation 生命周期：整个聊天持续存在

------------------------------------------------------------------------

## 三、长期数据（Persistent）与临时数据（Temporary）

### 长期数据

下一轮聊天仍然需要的数据。

例如：

-   conversation_id
-   user_id
-   messages
-   summary
-   memory

例如：

第一轮：

    用户：我叫张三

第二轮：

    用户：我叫什么？

如果 messages 不保留，LLM 就不知道答案。

------------------------------------------------------------------------

### 临时数据

仅当前 Graph 运行需要的数据。

例如：

-   tool_result
-   retrieved_docs
-   retry_count
-   current_node
-   trace_id

例如：

    用户：查订单123

    ↓

    Tool 返回：已发货

    ↓

    LLM 回复

下一轮：

    帮我写邮件

订单查询结果已经没有意义。

------------------------------------------------------------------------

## 四、Checkpointer 在哪里起作用？

没有 Checkpointer：

    Request1
    ↓

    State

    ↓

    结束（丢失）

第二次请求：

重新创建一个全新的 State。

------------------------------------------------------------------------

有 Checkpointer：

    Request1

    ↓

    State

    ↓

    保存到 PostgreSQL

第二次请求：

    conversation_id

    ↓

    恢复 State

    ↓

    继续执行

这样聊天历史才能连续。

------------------------------------------------------------------------

## 五、为什么说 State 不是数据库？

错误理解：

    State = Redis

实际上：

State 只是一次 Graph 的上下文。

数据库保存的是：

-   用户配置
-   长期记忆
-   聊天记录

State 是：

> Graph 当前运行时需要共享的数据。

------------------------------------------------------------------------

# 六、State 中不要放什么？

不要放资源：

❌

-   ChatOpenAI
-   Redis Client
-   PostgreSQL Session
-   Checkpointer
-   Embedding
-   Graph

资源属于：

    Container

    ↓

    Factory

    ↓

    Node

Node 自己拿资源。

State 只保存数据。

------------------------------------------------------------------------

# 七、推荐的 State 设计原则

## 1. 按业务流程设计

例如：

    用户输入

    ↓

    Planner

    ↓

    Retriever

    ↓

    Tool

    ↓

    LLM

    ↓

    Answer

State：

``` python
class ChatState(TypedDict):
    user_input: str
    intent: str
    retrieved_docs: list[str]
    tool_results: list[str]
    answer: str
```

而不是：

``` python
llm
redis
db
```

------------------------------------------------------------------------

## 2. 一个字段只负责一种含义

不要：

``` python
state["result"]
```

应该：

``` python
state["search_results"]
state["tool_results"]
state["summary"]
```

字段要表达业务意义。

------------------------------------------------------------------------

## 3. 一个字段不要承担多个阶段

错误：

    message

    ↓

    用户输入

    ↓

    改成 Tool 返回

    ↓

    改成 LLM 输出

推荐：

    user_message
    rewritten_query
    tool_result
    answer

------------------------------------------------------------------------

## 4. 一个 Node 只关心自己需要的字段

Planner：

输入：

    message

输出：

    intent

Tool：

输入：

    intent

输出：

    tool_result

LLM：

输入：

    message
    tool_result

输出：

    answer

做到高内聚。

------------------------------------------------------------------------

## 5. 不保存可以重新计算的数据

例如：

Retriever：

    vector.search()

    ↓

    docs

如果后续不再使用 docs，就不要一直保留。

避免 State 无限膨胀。

------------------------------------------------------------------------

## 6. State 尽量分组

不要：

``` python
class ChatState(TypedDict):
    message: str
    docs: list
    retry: int
    tool_results: list
```

推荐：

``` python
from dataclasses import dataclass

@dataclass
class SearchContext:
    query: str
    documents: list[str]

@dataclass
class ToolContext:
    calls: list
    results: list

@dataclass
class RuntimeContext:
    retry: int = 0
    current_node: str = ""

class ChatState(TypedDict):
    conversation_id: str
    user_id: str
    message: str
    search: SearchContext
    tool: ToolContext
    runtime: RuntimeContext
    answer: str
```

这样维护成本低很多。

------------------------------------------------------------------------

# 八、State 三层模型（推荐）

    ChatState
    │
    ├── Conversation
    ├── Runtime
    └── Business

Conversation：

    conversation_id
    user_id
    messages
    summary
    memory

Runtime：

    retry_count
    current_node
    trace_id

Business：

    planner
    search
    tool
    answer

职责清晰。

------------------------------------------------------------------------

# 九、生命周期理解（最重要）

    HTTP Request
    │
    ├── Runtime Context（新建）
    │
    ├── Graph 执行
    │
    ├── Runtime 销毁
    │
    └── Request 结束

Conversation：

    Conversation

    ↓

    messages

    ↓

    summary

    ↓

    memory

    ↓

    一直存在

因此：

-   Runtime 每个请求都是新的
-   Conversation 可以持续几个月

------------------------------------------------------------------------

# 十、生产环境不会无限保存 messages

真正项目通常不是：

    messages
    一直追加

而是：

    最近 N 轮 Messages
    +
    Summary（历史摘要）
    +
    Memory（长期事实）

这样可以控制 Token，并提高模型推理效率。

------------------------------------------------------------------------

# 十一、最终牢记一句话

> **State 不是数据库，不是资源容器，而是一张在 Graph 中不断被各个 Node
> 填写和传递的"工作单"。**

Node 不需要知道前一个 Node 是谁，也不需要调用下一个 Node。

它只需要：

1.  读取自己需要的数据
2.  修改自己负责的数据
3.  返回新的 State

Graph 负责调度整个执行流程。

这也是 LangGraph 易扩展、易维护的核心思想。
