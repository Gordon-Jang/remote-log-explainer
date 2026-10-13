# Changelog

## v0.4.0

- 新增文件/文件夹占用定位：`lockwho <path>` 可显示占用程序、PID、程序路径和匹配句柄。
- 文件检查优先使用 Windows Restart Manager；目录检查使用微软官方 Sysinternals Handle。
- 安装器从 Microsoft 官方地址下载 `handle64.exe`，并验证 Authenticode 签名为 Microsoft Corporation；二进制不提交到仓库。
- Remote Monitor 可自动识别 WinError 32 / sharing violation / “另一个进程正在使用”等占用错误，并记录相关路径。
- Monitor 新增 `L` 热键查看最近一次占用，`K` 热键选择终止占用进程。
- 终止操作必须二次确认，并拒绝终止关键 Windows 系统进程。
- 新增手动终止：`lockwho <path> --kill <PID>`；可用 `--yes` 跳过 CLI 的确认。
- 当前单元测试扩展到 11 项。

## v0.3.5

- 修复 `remote` 在 Desktop Commander 新版本首次下载时可能卡住的问题：内部统一改为 `npx --yes`。
- 启动器不再假定固定版本；默认使用 `@latest`，也支持并保留显式版本，如 `@0.2.52`。
- PowerShell 的 npx hook 现在可识别带 `--yes` / `-y` 和任意 Desktop Commander 版本的 remote 命令。
- 新增 runner 单元测试，验证非交互启动与版本透传。

## v0.3.4

- 修复经典 Windows 控制台固定 BufferSize 导致可滚动空白背景的问题。
- Remote 与 Monitor 优先在 Windows Terminal 中启动，使用动态 scrollback。
- 不限制历史长度，也不再修改 BufferSize。
- 移除 Clear-Host；Windows Terminal 下用 OSC 设置默认黑色背景，避免额外生成空白行。
- Windows Terminal 不可用时保留经典控制台回退。

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
