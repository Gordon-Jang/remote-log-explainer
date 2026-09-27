# Changelog

## v0.3.3

- 修复 v0.3.2 把控制台 BufferSize 固定为 1000 行后产生大量可滚动空白的问题。
- 不再修改 Remote / Monitor 的历史长度或缓冲区高度。
- 保留黑色背景与状态颜色，历史由终端自身正常管理。

## v0.3.2

- Remote 与 Monitor 默认改为黑色背景和灰色正文。
- 两个控制台的滚动历史限制为 1000 行，超过后自动丢弃最旧内容。
- 新增共享的 `console-style.ps1`，统一控制两个窗口的终端外观和缓冲区。

## v0.3.1

- 修复 Windows 控制台 ANSI 转义码被直接显示的问题。
- 优先启用 VT/ANSI；不可用时回退到 Windows Console API。
- 保留成功、信息、运行中、警告、错误、辅助信息的颜色区分。

## v0.3.0

- 支持直接输入 `remote` 启动 Remote + Monitor。
- 支持 PowerShell 中原始 `npx @wonderwhy-er/desktop-commander@latest remote` 自动带起 Monitor。
- 普通 `npx` 命令保持原始 npm 行为。
- 增加可恢复的 `npx.ps1` 备份与卸载逻辑。
- 新 Remote 使用独立 stdout/stderr 会话流，减少并发会话串日志。
- 支持 `origin_instance` 来源显示。

## v0.2.0

- 增加 Remote stdout/stderr tee 运行器。
- 增加实时 Remote 原始行解析。
- 移除隐藏 watcher、Startup 自启与 Windows Terminal 参数方案。
- 改为透明、可见的 Remote/Monitor 双窗口模式。

## v0.1.0

- 初始规则解释器。
- 支持 Desktop Commander `tool-history.jsonl`。
- 支持文件、进程、Git、超时与凭据脱敏规则。
