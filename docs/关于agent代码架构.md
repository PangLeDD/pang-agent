

**没错！** 这就是很多人第一次自己写 Container 时遇到的问题。

例如最开始：

```python
class AppContainer:

    def __init__(self):
        self.chat_service = ChatService()
```

后来：

```python
class AppContainer:

    def __init__(self):
        self.chat_service = ChatService()
        self.llm = OpenAI()
        self.redis = Redis()
        self.pg = Postgres()
        self.memory = Memory()
        self.embedding = Embedding()
        self.tool_registry = ToolRegistry()
        self.prompt_manager = PromptManager()
        self.graph = Graph()
```

最后变成：

```python
class AppContainer:
    def __init__(self):
        ...
        200 行
```

这不就是把 Spring 的 IoC 容器自己重新写了一遍吗？

**所以，大型项目根本不会这样写。**

---

# 第一种演进：Container 只管理顶层对象（⭐⭐⭐⭐⭐ 推荐）

很多人的误区是：

> **所有对象都放 Container。**

其实不是。

Container 只管理：

> **真正需要全局共享（Singleton）的对象。**

例如：

```
Container
├── Redis
├── Postgres
├── OpenAI Client
├── ToolRegistry
└── PromptRegistry
```

只有这些。

而：

```
ChatService
MemoryService
GraphService
```

都不要存。

为什么？

因为它们可以临时创建。

例如：

```python
class Container:

    def __init__(self):

        self.redis = Redis(...)
        self.llm = OpenAI(...)
        self.tool_registry = ToolRegistry()
```

然后：

```python
def get_chat_service(container: Container):

    return ChatService(
        llm=container.llm,
        tools=container.tool_registry,
    )
```

ChatService 每次请求都创建。

OpenAI 永远只有一个。

Redis 永远只有一个。

---

## 第二种演进：拆 Container

这个就很像 Java Config。

例如：

```
container
│
├── infrastructure.py
├── ai.py
├── service.py
└── application.py
```

例如：

### AIContainer

```python
class AIContainer:

    def __init__(self):

        self.llm = OpenAI()

        self.embedding = Embedding()
```

---

### InfraContainer

```python
class InfraContainer:

    def __init__(self):

        self.redis = Redis()

        self.pg = AsyncPG()
```

---

### ToolContainer

```python
class ToolContainer:

    def __init__(self):

        self.registry = ToolRegistry()
```

---

最后：

```python
class AppContainer:

    def __init__(self):

        self.ai = AIContainer()

        self.infra = InfraContainer()

        self.tools = ToolContainer()
```

是不是一下舒服很多？

---

# 第三种演进：Provider（我最喜欢）

其实 Container 不存对象。

而是存：

> **如何创建对象。**

例如：

```python
class LLMProvider:

    def get(self):

        if settings.provider == "openai":

            return OpenAI()

        return Qwen()
```

Container：

```python
class Container:

    def __init__(self):

        self.llm_provider = LLMProvider()
```

然后：

```python
class ChatService:

    def __init__(self, provider: LLMProvider):

        self.provider = provider
```

需要的时候：

```python
llm = self.provider.get()
```

Container 根本不用存：

```
OpenAI

Azure

Claude

DeepSeek
```

---

# 第四种演进：依赖注册（真正成熟）

很多大型项目最后都会变成：

```python
container.register(
    LLM,
    OpenAI()
)

container.register(
    Redis,
    Redis(...)
)

container.register(
    PromptManager,
    PromptManager()
)
```

获取：

```python
container.resolve(LLM)
```

Container 根本不知道成员变量。

内部其实就是：

```python
class Container:

    def __init__(self):

        self._instances = {}
```

注册：

```python
def register(

    self,

    cls,

    instance,

):

    self._instances[cls] = instance
```

获取：

```python
def resolve(cls):

    return self._instances[cls]
```

是不是发现：

成员变量没有了。

只有：

```
_instances
```

一个 dict。

---

# 第五种演进：这其实就是 IoC

Spring：

```
BeanFactory

↓

Map<Class, Bean>
```

Python：

```
Container

↓

dict[type, object]
```

本质一样。

只是 Spring 帮你：

```
扫描

↓

实例化

↓

放 Map
```

Python：

你自己：

```
注册

↓

放 dict
```

---

# 那 AI Agent 最推荐哪一种？

如果是你现在的项目（我记得你前面聊过，有：

* LangGraph
* Checkpointer
* Memory
* FastAPI
* 多 LLM Provider
* Agent 开发

这种规模。）

**我不会自己写一个"超级 Container"。**

我会这样分：

```
AppContainer
│
├── InfraContainer
│   ├── postgres
│   ├── redis
│   └── checkpointer
│
├── AIContainer
│   ├── llm_factory
│   ├── embedding_factory
│   └── prompt_manager
│
├── ToolContainer
│   └── registry
│
└── ServiceFactory
    ├── create_chat_service()
    ├── create_graph_service()
    └── create_memory_service()
```

你会发现：

* **Container** 管理共享资源（生命周期长）。
* **Factory** 负责创建业务对象（生命周期短）。

这是两个不同的职责。

---

## 我反而想给你介绍一个概念，我觉得它会彻底打开你的思路

你现在一直在想：

> **Container 里面放什么？**

而我现在做 AI Agent 项目，更常想的是：

> **"这个对象到底应该活多久（Object Lifetime）？"**

这和 Spring 里的 Bean Scope 非常像。

例如：

| 对象              | 生命周期 | 放哪里        |
| --------------- | ---- | ---------- |
| OpenAI Client   | 整个应用 | Container  |
| Redis Client    | 整个应用 | Container  |
| Checkpointer    | 整个应用 | Container  |
| ToolRegistry    | 整个应用 | Container  |
| ChatService     | 每个请求 | Factory 创建 |
| LangGraph State | 每次对话 | Factory 创建 |
| 当前用户上下文         | 每个请求 | Depends    |

**真正决定设计的不是"它属于哪个模块"，而是"它应该活多久"。**

我觉得这是 Java 开发者转到 Python/FastAPI 后，最值得建立的思维方式。一旦按照生命周期来划分，你会发现 Container 自然不会越来越臃肿，因为只有真正需要长期存在的对象才值得放进去。
