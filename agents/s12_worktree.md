Git Worktree 是一项高效功能，它允许开发者在同一个仓库中同时开启多个独立的物理目录（工作区），而无需频繁地 `git stash` 或 `git checkout`。

### 一、使用 Worktree 的核心场景

1. **并行开发与对比 (Parallel Development/Comparison)**
   - 在开发新特性（Feature）的同时，需要立即处理一个紧急 Bug（Hotfix），或者需要同时在不同分支间对比代码。
   - 适合 AI 场景下进行多 Agent 并行试错、对比和提交。
2. **避免频繁切换导致的依赖冲突 (Solving Dependency Conflicts)**
   - 当不同分支依赖不同版本的依赖包（例如 `node_modules`）时，使用 worktree 可以将不同项目版本放在不同的目录中，无需在切换分支后重新安装依赖。
3. **同时开发不同版本 (Maintaining Multiple Versions)**
   - 项目同时维护主干（main）、测试（develop）和旧版本（maint）分支，worktree 可以让这些分支同时以文件夹形式存在。
4. **PR Review (Pull Request Reviews)**
   - 在不破坏当前本地工作区的前提下，在另一个工作目录中 Checkout 他人的 PR 分支进行查看、测试。 [[1](https://zhuanlan.zhihu.com/p/2017144122020999473), [2](https://dailypypy.org/learn/git-worktree/), [3](https://juejin.cn/post/7125293870891401224), [4](https://blog.csdn.net/entronad/article/details/81324147), [5](https://blog.csdn.net/mrbone11/article/details/148934172)]

### 二、Worktree 的限制与注意事项

1. **分支独占限制 (Branch Exclusivity)**
   - **限制**：一个分支同一时间只能被一个 worktree checkout。不能在两个不同的 worktree 中同时 checkout 同一个分支。
   - **解决**：如果需要同时使用，需创建新的分支或在其中一个 worktree 中切换到其他分支。
2. **路径管理**
   - 工作树是不同的物理文件夹，需要分别管理和清理，不能直接删除工作树文件夹，需要使用 `git worktree remove` 命令来清理。
3. **配置共享**
   - 附加的 worktree 共享父仓库的配置、Remote 和 Hook，修改这些配置会影响所有 worktree。 [[1](https://www.termdock.com/zh/blog/git-worktree-multi-agent-setup), [2](https://www.xmsumi.com/detail/2955), [3](https://cloud.tencent.com/developer/article/2653851), [4](https://zhuanlan.zhihu.com/p/2017144122020999473), [5](https://dailypypy.org/learn/git-worktree/)]

### 三、Worktree 解决的是“切换环境的成本”

所谓“切换环境的成本”，在 Git 开发中主要由**磁盘状态（Artifacts）**和**心理负担（Mental Context）**两部分组成。Worktree 本质上是通过“空间换时间”的策略，把这两项成本降到了最低。

我们可以从以下三个深度维度来理解：

#### 1.消除“编译与构建”的等待时间（Artifacts Cost）

这是最硬核的成本。

- **普通模式（Checkout）**：当你从 `feature-A` 切换到 `feature-B` 时，虽然 Git 只改了源码，但你的编译器或打包工具（如 Webpack, Maven, Go build）会发现文件时间戳变了。切换回来后，往往需要**重新编译**或重新安装依赖（`npm install`），这可能耗费数分钟。
- **Worktree 模式**：每个 Worktree 都有自己独立的构建产物、日志和临时文件。你在 A 目录编译好的 `.o` 或 `node_modules` 永远在那。**切换分支变成了物理上的“进入另一个文件夹”**，耗时为 0。

#### 2. 维持“运行时状态”的连续性（Runtime Cost）

如果你正在调试一个复杂的 Bug：

- **普通模式**：你必须关掉正在运行的服务，`git stash` 掉断点和打印语句，切走处理紧急任务，回来后再还原、重启服务、重新登录到刚才的页面。
- **Worktree 模式**：你可以让 Feature A 的服务在端口 8080 继续跑着，直接在另一个文件夹（Feature B）起一个 8081 的服务。**你不需要中断调试过程**，两边的内存状态、数据库连接和浏览器 Tab 都可以并存。

#### 3.避免“储藏栈”的混乱（Mental Context Cost）

- **普通模式**：频繁使用 `git stash` 会导致你的储藏栈里堆满了“无名记录”。当你处理完紧急 Bug 回来时，可能已经忘了 `stash@{2}` 里面到底改了 `config.py` 的哪一部分。
- **Worktree 模式**：由于不需要 Stash，你的工作现场是“物理保活”的。你的 IDE 窗口、打开的文件标签、甚至你在编辑器里还没保存的临时笔记，都在那个特定的窗口里纹丝不动。**这种“视觉上的语义化隔离”极大降低了大脑重载上下文的压力。**

深度对比总结：

| 维度           | Git Checkout + Stash           | Git Worktree                     |
| -------------- | ------------------------------ | -------------------------------- |
| **切换速度**   | 快（仅源码）                   | 极快（瞬间移动目录）             |
| **构建成本**   | 高（频繁重编 / 重新安装依赖）  | **极低（每个目录保留产物）**     |
| **调试连续性** | 会中断（必须停止当前运行进程） | **不中断（并行运行多个实例）**   |
| **清理成本**   | 低（只有一个目录）             | 高（需要手动 `remove` 遗留目录） |

