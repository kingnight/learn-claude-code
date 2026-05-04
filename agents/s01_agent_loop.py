#!/usr/bin/env python3
# Harness: the loop -- the model's first connection to the real world.
"""
s01_agent_loop.py - The Agent Loop

The entire secret of an AI coding agent in one pattern:

    while stop_reason == "tool_use":
        response = LLM(messages, tools)
        execute tools
        append results

    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)

This is the core loop: feed tool results back to the model
until the model decides to stop. Production agents layer
policy, hooks, and lifecycle controls on top.
"""

import os
import subprocess

try:
    import readline
    # #143 UTF-8 backspace fix for macOS libedit
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
    readline.parse_and_bind('set enable-meta-keybindings on')
except ImportError:
    pass

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}]


def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"


# -- The core pattern: a while loop that calls tools until the model stops --
def agent_loop(messages: list):
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})
        # If the model didn't call a tool, we're done
        if response.stop_reason != "tool_use":
            return
        # Execute each tool call, collect results
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\033[33m$ {block.input['command']}\033[0m")
                output = run_bash(block.input["command"])
                print(output[:200])
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": output})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    # Shared message list: agent_loop appends assistant turns and tool-result user turns in place.
    history = []
    while True:
        try:
            # 先打印一行带颜色的 s01 >> ，光标停在这行末尾，然后 input() 读取你敲的一整行，返回值赋给 query。
            # 若没有这个参数，等价于 input("")，就不会先打印任何提示。
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            # Ctrl+D / Ctrl+C — exit without traceback
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)  # mutates history until stop_reason != tool_use
        # Last turn is assistant; content may be a list of blocks (text, tool_use, …).
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)  # bash output was already printed inside agent_loop
        print()


"""
外层（if __name__ == "__main__" 里的 while True）

* 作用：交互式会话：读一行用户输入 → 跑一轮任务 → 再读下一行。
* 结束条件：用户输入 q / exit / 空行，或 Ctrl+C / Ctrl+D。
* 若没有这层，程序跑完一次对话就会直接退出，没法连续多问。

内层（agent_loop 里的 while True）

* 作用：单次用户请求内部的「模型 ↔ 工具」闭环：只要 stop_reason == "tool_use"，就执行工具、把结果写回 messages、再调 API，直到模型不再要工具。
* 结束条件：response.stop_reason != "tool_use"（模型给出最终答复或不再调用工具）。
* 这是脚本开头注释里画的那个 agent 核心模式；一轮用户消息里可能有多轮 API 调用。

关系可以概括成：

会话层：while True          # 多轮「用户提问」
  └── 任务层：agent_loop     # 每一问里可能多次「要工具 → 执行 → 再要模型」
所以不是「同一个死循环写了两遍」，而是 外层管「要不要接着聊」，内层管「这一问里要不要接着用工具」；
职责分离是合理且常见的写法。若强行合成一个 while，反而要把「读 input」和「调模型 / 跑工具」搅在一起，更难读。

"""