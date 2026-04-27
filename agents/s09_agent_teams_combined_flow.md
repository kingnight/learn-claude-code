# s09 Agent Teams 组合流程图

本文档描述 `TeammateManager` 与 `MessageBus` 在 `agents/s09_agent_teams.py` 中的协作流程。

```mermaid
flowchart LR
    Lead[Lead/主Agent] -->|spawn_teammate| TM[TeammateManager.spawn]
    TM --> CFG[(.team/config.json)]
    TM --> TH[启动 teammate 线程]

    TH --> LOOP[_teammate_loop]
    LOOP -->|"read_inbox(name)"| MB_READ[MessageBus.read_inbox]
    MB_READ --> INBOX[(.team/inbox/name.jsonl)]
    MB_READ --> LOOP

    LOOP --> LLM[client.messages.create]
    LLM -->|tool_use: send_message| EXEC[_exec]
    EXEC -->|BUS.send| MB_SEND[MessageBus.send]
    MB_SEND --> INBOX2[(.team/inbox/other.jsonl)]

    Lead -->|send_message / broadcast| MB_SEND
    Lead -->|"read_inbox(lead)"| MB_READ_LEAD[MessageBus.read_inbox]
    MB_READ_LEAD --> LEADBOX[(.team/inbox/lead.jsonl)]

    LOOP --> ENDCHK{循环结束或非tool_use/异常}
    ENDCHK --> STATUS["成员状态->idle(非shutdown)"]
    STATUS --> CFG
```

## 关键说明

- `TeammateManager` 负责队友生命周期（创建线程、状态维护、配置落盘）。
- `MessageBus` 负责消息投递与收件箱读取（读取后即清空，属于 drain 语义）。
- Lead 与 Teammate 都通过 `MessageBus` 间接通信，不直接共享会话上下文。
