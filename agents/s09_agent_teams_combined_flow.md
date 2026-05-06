## s09_agent_teams 软件流程图

```mermaid
flowchart TD
    START([程序启动]) --> INIT[初始化,MessageBus / TeammateManager,加载 .team/config.json]
    INIT --> REPL_LOOP{读取用户输入}

    REPL_LOOP -->|/team| LIST_TEAM[打印团队成员列表] --> REPL_LOOP
    REPL_LOOP -->|/inbox| READ_LEAD_INBOX[读取 lead 收件箱] --> REPL_LOOP
    REPL_LOOP -->|q / exit| END([退出])
    REPL_LOOP -->|普通指令| APPEND_MSG[追加到 history,role=user]

    APPEND_MSG --> AGENT_LOOP

    subgraph AGENT_LOOP["agent_loop — Lead 主循环"]
        direction TB
        AL_START([进入循环])
        AL_START --> CHECK_INBOX[BUS.read_inbox lead,读取并清空 lead.jsonl]
        CHECK_INBOX -->|有消息| INJECT[注入 inbox 消息到 messages]
        CHECK_INBOX -->|无消息| API_CALL
        INJECT --> API_CALL[调用 Anthropic API]
        API_CALL --> APPEND_RESP[追加 assistant 响应到 messages]
        APPEND_RESP --> STOP_CHECK{stop_reason == tool_use?}
        STOP_CHECK -->|否| AL_END([返回])
        STOP_CHECK -->|是| EXEC_TOOL[执行工具,spawn_teammate / send_message / broadcast ...]
        EXEC_TOOL --> COLLECT[收集 tool_result 追加到 messages]
        COLLECT --> AL_START
    end

    subgraph TEAMMATE_MANAGER["TeammateManager — 成员生命周期"]
        direction TB
        subgraph SPAWN["spawn(name, role, prompt)"]
            direction TB
            SP_START([spawn 调用]) --> FIND_MEMBER{成员已存在?}
            FIND_MEMBER -->|是| CHECK_STATUS{status == idle / shutdown?}
            CHECK_STATUS -->|否| SP_ERR([返回 Error])
            CHECK_STATUS -->|是| UPDATE_STATUS[更新 status=working 更新 role]
            FIND_MEMBER -->|否| NEW_MEMBER[创建新成员 status=working]
            UPDATE_STATUS --> SAVE_CFG[保存 config.json]
            NEW_MEMBER --> SAVE_CFG
            SAVE_CFG --> START_THREAD[启动 daemon Thread]
            START_THREAD --> SP_END([返回 Spawned])
        end

        subgraph TEAMMATE_LOOP["_teammate_loop — 子线程"]
            direction TB
            TL_START([线程启动]) --> BUILD_SYS[构建 sys_prompt,初始化 messages]
            BUILD_SYS --> TL_ITER{最多 50 轮}
            TL_ITER -->|超限| TL_IDLE
            TL_ITER -->|继续| TL_INBOX["BUS.read_inbox(name),读取并清空 name.jsonl"]
            TL_INBOX -->|有消息| TL_INJECT[注入消息到 messages]
            TL_INBOX -->|无消息| TL_API
            TL_INJECT --> TL_API[调用 Anthropic API]
            TL_API -->|异常| TL_IDLE
            TL_API --> TL_APPEND[追加 assistant 响应]
            TL_APPEND --> TL_STOP{stop_reason == tool_use?}
            TL_STOP -->|否| TL_IDLE[status → idle,保存 config.json]
            TL_STOP -->|是| TL_EXEC[执行工具,bash/read/write/edit,send_message/read_inbox]
            TL_EXEC --> TL_RESULTS[收集 tool_result 追加到 messages]
            TL_RESULTS --> TL_ITER
            TL_IDLE --> TL_END([线程结束])
        end
    end

    subgraph MESSAGE_BUS["MessageBus — JSONL 文件通信"]
        direction TB
        MB_SEND["send(sender, to, content, type),→ 追加一行 JSON 到 to.jsonl"]
        MB_FILE[(inbox/name.jsonl)]
        MB_READ["read_inbox(name),→ 读取 → 清空 → 返回列表"]
        MB_BC["broadcast(sender, content, teammates),→ 对每个非 sender 成员调用 send"]
        MB_SEND -->|写入| MB_FILE
        MB_READ -->|读取并清空| MB_FILE
        MB_BC --> MB_SEND
    end

    AL_END --> PRINT[打印最终文本响应] --> REPL_LOOP
```

### 关键设计要点

| 概念 | 说明 |
|------|------|
| **MessageBus** | 纯文件 JSONL，append 写入、读后清空，天然解耦发送方与接收方 |
| **TeammateManager** | 维护 config.json 状态机，spawn 复用已有成员或新建，每人独立 daemon 线程 |
| **状态机** | 成员状态：`working → idle → working`（可复用）或 `shutdown`（s10 扩展） |
| **Lead 主循环** | 单线程 REPL，每轮先检查自己的收件箱，再调用 API |
| **Teammate 子线程** | 每个成员独立 daemon 线程，最多 50 轮对话后自动变 idle |
| **消息类型** | 5 种类型在此文件声明，`shutdown_*` 和 `plan_approval_response` 留给 s10 实现 |
