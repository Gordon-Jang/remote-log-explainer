# Remote Log Explainer

Desktop Commander Remote 的本地实时日志解释器。

## 目标

- 把 Remote 的工具调用、JSON 和进程输出转换成简短中文状态。
- 默认完全不使用大模型，也不访问云端。
- 监控窗口独立显示，效果接近 Codex 的实时执行反馈。
- 原始日志默认隐藏，需要时按 R 展开。
- 自动隐藏常见 token、API key、Authorization 和密码。
- Remote 结束后监控窗口自动结束。

## 透明运行

当前版本不使用隐藏 watcher、不写 Windows Startup、不创建计划任务，
也不修改 Desktop Commander 源码。

早期原型曾使用 Startup + 隐藏 PowerShell，并且 Windows Terminal 参数转义有问题，
会连续打开报错标签页。该方案已经删除，安装脚本会清理旧 Startup 项和旧 watcher。

## 两种监控模式

### 1. 推荐：从本工具启动 Remote

运行：

powershell -ExecutionPolicy Bypass -File "$HOME\.remote-log-explainer\scripts\remote-with-monitor.ps1"

它会打开两个可见终端：

- Desktop Commander Remote：正常显示 Remote 原始输出。
- Remote Monitor：实时显示中文解释。

Remote 的 stdout/stderr 会同时写入当前会话自己的 UTF-8 日志，
Monitor 解析的就是这一份日志，因此不会把别的 Remote 终端日志混进来。
日志中还能保留 Remote 输出里的 origin_instance，用于区分不同来源会话。

### 2. 兼容：附加到已经运行的 Remote

运行：

powershell -ExecutionPolicy Bypass -File "$HOME\.remote-log-explainer\scripts\attach-monitor.ps1"

Desktop Commander 无法让外部进程重新接管一个已经启动的控制台 stdout，
所以这个模式读取它现有的：

%USERPROFILE%\.claude-server-commander\tool-history.jsonl

这个文件是共享历史。如果同时有多个对话在使用同一个 Remote，
兼容模式可能显示多个对话的工具调用。下次改用上面的“从本工具启动 Remote”
即可获得独立的实时流。

## 安装

在仓库根目录：

powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1

部署到：

%USERPROFILE%\.remote-log-explainer

安装只复制文件并清理旧原型，不创建登录自启，不启动隐藏进程。

## 终端快捷键

- R：显示/隐藏原始 JSON 或原始 Remote 行
- C：清屏
- Q：退出监控

## 规则解释

当前版本只使用 Python 标准库和 PowerShell，覆盖：

- read_file / write_file / edit_block / list_directory
- start_process / read_process_output / interact_with_process
- 进程 PID、完成、仍在运行、等待新输出
- Python unittest 测试通过数量
- Git LF/CRLF 警告
- request timed out / WebSocket 到 HTTPS 回退
- Remote 配置读取与修改
- origin_instance 会话来源
- 常见凭据脱敏

只有规则无法覆盖的日志积累到确实需要时，才考虑可选的本地小模型兜底。

## 测试

python -m py_compile .\src\remote_log.py .\src\remote_runner.py
python -m unittest discover -s tests -v

PowerShell 脚本也必须通过 Parser 静态语法检查。

版本：0.2.0
