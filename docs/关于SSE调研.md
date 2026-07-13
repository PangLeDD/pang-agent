在 AI Agent 开发里，**SSE（Server-Sent Events）已经成为流式输出的主流方案**，尤其是类似 ChatGPT、Claude、Cursor 这种「边生成边展示」的产品。

但是要注意一点：

> SSE 本身只规定了传输格式，不规定你的业务事件长什么样。

所以真正需要后端和前端约定的是：

* event 类型
* data JSON 结构
* message 生命周期
* Agent 状态变化
* tool 调用过程
* 最终结果

目前比较主流的设计，基本都趋向于 **Event-driven SSE 协议**。

---

# 1. 最基础 SSE 格式

SSE 原生格式：

```
event: xxx
data: xxx

```

例如：

```
event: message
data: hello


event: message
data: world

```

浏览器收到：

```
hello
world
```

---

但是 AI Agent 不会这么简单。

因为 Agent 有：

* 思考
* 调工具
* 查知识库
* 多步骤执行
* 生成回答

所以一般会设计事件流。

---

# 2. 主流 Agent SSE 事件模型

比较常见：

```
event: start
event: thinking
event: tool_call
event: tool_result
event: message
event: done
event: error
```

完整生命周期：

```
用户输入
   |
   |
 SSE连接建立
   |
   |
 event:start
   |
   |
 event:thinking
   |
   |
 event:tool_call
   |
   |
 event:tool_result
   |
   |
 event:message
   |
   |
 event:done
```

---

# 3. 推荐的数据结构

比如：

## 开始事件

后端：

```
event: start
data:
{
    "conversation_id":"abc123",
    "message_id":"msg001"
}

```

前端：

```javascript
switch(event.type){

case "start":
    createMessage()
}
```

---

## Agent 思考状态

例如：

```
event: thinking

data:
{
    "status":"searching",
    "message":"正在查询知识库"
}

```

前端显示：

```
🤖 正在查询资料...
```

注意：

生产环境一般不会直接传：

```
我正在思考：
用户可能需要xxx
我的计划是xxx
```

而是状态。

例如：

```
thinking
planning
retrieving
executing
```

---

# 4. Token流（最核心）

ChatGPT 类产品核心：

```
event: message

data:
{
    "id":"msg001",
    "delta":"你好"
}

```

下一帧：

```
event: message

data:
{
    "id":"msg001",
    "delta":"，我是"
}

```

下一帧：

```
event: message

data:
{
    "id":"msg001",
    "delta":"AI助手"
}

```

前端：

```javascript
answer += delta
```

显示：

```
你好，我是AI助手
```

---

# 5. Tool Calling（Agent重点）

比如 Agent 调天气 API。

## 调用工具

后端：

```
event: tool_call

data:
{
    "tool":"weather",
    "arguments":{
        "city":"Tokyo"
    }
}

```

前端显示：

```
🔧 正在查询 Tokyo 天气
```

---

工具结果：

```
event: tool_result

data:
{
    "tool":"weather",
    "result":{
        "temperature":25
    }
}

```

---

# 6. 完成事件

最后：

```
event: done

data:
{
    "finish_reason":"stop",
    "usage":{
        "input_tokens":100,
        "output_tokens":300
    }
}

```

---

# 7. 一个比较完整的生产级 SSE 示例

实际可能长这样：

```
event: start
data:{
 "conversation_id":"c001"
}


event: agent_status
data:{
 "status":"planning"
}


event: tool_call
data:{
 "name":"search",
 "id":"tool001"
}


event: tool_result
data:{
 "id":"tool001",
 "success":true
}


event: message
data:{
 "delta":"根据查询结果"
}


event: message
data:{
 "delta":"今天东京天气晴朗"
}


event: done
data:{
 "reason":"complete"
}

```

---

# 8. 后端接口一般这样设计

例如 FastAPI：

```python
@app.post("/chat")
async def chat(req:ChatRequest):

    return StreamingResponse(
        agent_stream(),
        media_type="text/event-stream"
    )
```

流：

```python
async def agent_stream():

    yield """
event:start
data:{}
"""

    yield """
event:message
data:{
"delta":"hello"
}
"""

    yield """
event:done
data:{}
"""
```

---

# 9. 现在比较推荐的事件命名

我个人建议：

```
conversation.start

agent.status

agent.thought

tool.call

tool.result

message.delta

conversation.end

error
```

原因：

比：

```
start
message
done
```

更容易扩展。

例如未来：

多 Agent：

```
agent.status

{
 agent:"researcher",
 status:"searching"
}

```

非常自然。

---

# 10. 和 LangGraph / OpenAI Streaming 的关系

现在很多框架其实也是这个思想。

例如：

OpenAI streaming：

```
response.delta
response.completed
```

LangGraph：

```
node_start
node_end
messages
updates
```

本质都是：

> 把 Agent 执行过程暴露成事件流。

---

# 我比较推荐你的 AI Agent 项目采用这种协议

因为你之前聊过 Agent Memory、规划架构，我觉得不要只设计：

```
message
done
```

这种聊天级 SSE。

建议直接设计：

```
AgentEvent

{
    id,
    type,
    timestamp,
    payload
}

```

例如：

```json
{
  "id":"evt_001",
  "type":"tool.call",
  "timestamp":1720000000,
  "payload":{
      "tool":"database",
      "params":{
          "sql":"..."
      }
  }
}
```

这样未来：

* 多 Agent
* 工作流
* 人工介入 Human-in-loop
* Agent Replay
* 调试 Trace

都不用推翻协议。

简单总结：

> **普通聊天 SSE = message.delta + done**
>
> **AI Agent SSE = Event Stream（状态 + 工具 + 消息 + 生命周期）**

如果你是在做真正的 Agent 平台，我更建议按第二种设计。你后面做 Memory、Planner、Tool Executor 时会舒服很多。
