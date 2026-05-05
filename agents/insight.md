学完给我们带来哪些启示

$$Harness = Tools + Knowledge + Observation + Action \ Interfaces + Permissions$$​

1. 给模型提供有效且足够多的能够感知环境的支持是必要的，对应到iOS 开发
* build /test 结果，日志（对应Tools）
* 界面/布局信息（对应Observation）
* 项目背景信息（对应 Knowledge），比如什么是feed的tpl

这些是下一步的发力方向

2. 使用Claude code开发时
* 解决复杂问题时，优先使用/plan进行规划
* 合理使用subagent隔离上下文
* plan通过issue记录，任务一项完成迭代一次issue，关键方案（踩坑记录）同步更新，使得模型在任意时刻，在一个全新的干净上下文中，通过issue获得必要信息，顺利的继续任务执行

