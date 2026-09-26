# Remote Log Explainer

Desktop Commander Remote 的本地实时日志解释器。

## 现在的启动方式

下面两种输入都可以：

```powershell
npx @wonderwhy-er/desktop-commander@latest remote
```

或：

```powershell
remote
```

两种都会执行同一个流程：

`输入命令 → 启动/复用 Desktop Commander Remote → 打开 Remote Monitor`

如果 Remote 已经在运行，不会重复启动 Remote，只会确认 Monitor 已存在或附加 Monitor。

## 实现方式

没有 Startup、自启动服务、隐藏 watcher、计划任务或后台轮询。

- `remote`：通过 `E:\node\remote.cmd` 进入透明启动器。
- PowerShell 中的原始 `npx ... remote`：只对这一条 Desktop Commander Remote 命令做精确匹配。
- 其他 `npx` 命令继续执行原来的 npm `npx.ps1` 逻辑。
- 原始 `npx.ps1` 会备份为 `npx.remote-log-backup.ps1`，卸载时可恢复。

注意：Node/npm 更新可能重建 `npx.ps1`。如果更新后联动失效，重新运行本项目安装脚本即可恢复。
## Monitor

推荐的新会话模式会给每次 Remote 单独保存一份 UTF-8 实时流，再由 Monitor 解释，因此不会把多个 Remote 会话混在一起。

兼容已经运行中的旧 Remote 时，会读取 Desktop Commander 自己的共享 `tool-history.jsonl`；这种模式可能看到其他并发会话的工具记录。

终端快捷键：

- `R`：显示/隐藏原始 JSON 或原始 Remote 行
- `C`：清屏
- `Q`：退出 Monitor

## 规则解释

当前版本不用大模型，只使用 Python 标准库和 PowerShell，覆盖：

- 文件读取、写入、编辑和目录查看
- 进程启动、PID、完成、仍在运行、等待输入
- Python unittest 通过数量
- Git LF/CRLF 警告
- 超时和 WebSocket → HTTPS 回退
- Remote 配置操作
- `origin_instance` 会话来源
- 常见凭据脱敏

## 安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

部署目录：

`%USERPROFILE%\.remote-log-explainer`

安装脚本会安装两个命令入口，但不会创建登录自启或常驻进程。

## 卸载

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.remote-log-explainer\scripts\uninstall.ps1"
```

卸载会恢复备份的 `npx.ps1`，删除 `remote.cmd`，并移除运行时目录。

## 测试

```powershell
python -m py_compile .\src\remote_log.py .\src\remote_runner.py
python -m unittest discover -s tests -v
```

版本：0.3.0
