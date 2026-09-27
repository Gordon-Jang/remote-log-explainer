# Remote Log Explainer

一个面向 Windows 的 Desktop Commander Remote 本地实时日志解释器。

它把 Remote 控制台里的工具调用、JSON、进程状态和常见错误，转换成更接近 Codex 的中文实时反馈；默认 **0 大模型、0 云端日志分析、0 后台驻留**。

当前版本：`v0.3.3`

## 主要特点

- 输入 `remote` 即可启动 Desktop Commander Remote + Remote Monitor。
- 在 PowerShell 中输入原命令 `npx @wonderwhy-er/desktop-commander@latest remote` 也会自动带起 Monitor。
- Remote 已经运行时不会重复启动，只附加/复用一个 Monitor。
- 规则解释优先：不调用大模型，不发送日志到外部服务。
- 支持工具调用、文件操作、进程 PID、测试结果、超时、网络回退、Git 警告等常见状态。
- 支持 `origin_instance`，新会话模式可区分不同 Remote 来源。
- 常见 API key、token、Authorization、password 会在显示前脱敏。
- Windows 控制台颜色兼容：绿色成功、青色信息、紫色运行中、黄色警告、红色错误、灰色辅助信息。
- Remote 与 Monitor 默认使用黑色背景，但不修改终端历史长度；避免人为放大控制台缓冲区造成大量可滚动空白。
- 不写 Windows Startup、不创建计划任务、不启动隐藏 watcher。

## 效果示例

```text
13:34:51  • 开始 · 启动命令
          python -m unittest discover -s tests -v
          会话：muf6iwb9-eo6gjp

13:34:51  ⏳ 命令仍在运行 · PID 35776
          当前工具判断它可能在等待输入；不等于程序卡死
          测试通过：2 项

13:34:51  ✓ Remote 已结束 · exit 0
```

## 环境要求

- Windows 10 / 11
- PowerShell 5.1 或更高
- Python 3.9+
- Node.js / npm / npx
- 已能正常执行 Desktop Commander Remote

先确认下面命令本身可用：

```powershell
npx @wonderwhy-er/desktop-commander@latest remote
```

## 安装

克隆仓库：

```powershell
git clone https://github.com/Gordon-Jang/remote-log-explainer.git
cd remote-log-explainer
```

执行安装：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

安装后运行时文件位于：

```text
%USERPROFILE%\.remote-log-explainer
```

安装脚本不会创建登录自启或后台常驻服务。

## 日常使用

最简单的方式：

```powershell
remote
```

也可以继续使用 Desktop Commander 原命令：

```powershell
npx @wonderwhy-er/desktop-commander@latest remote
```

两种方式都会进入：

```text
输入命令
  ↓
启动 / 复用 Desktop Commander Remote
  ↓
打开 Remote Monitor
```

Monitor 快捷键：

- `R`：显示 / 隐藏原始 JSON 或原始 Remote 行
- `C`：清屏
- `Q`：退出 Monitor

更完整的安装、运行模式、更新和故障排查见：[docs/USAGE.zh-CN.md](docs/USAGE.zh-CN.md)。

## 两种监控模式

### 推荐：由本工具启动新的 Remote

`remote` 或原始 `npx ... remote` 在没有 Remote 运行时，会启动一份新的 Remote，并将该会话 stdout/stderr 同步写入独立 UTF-8 日志。

Monitor 只解析这一份会话日志，因此不会把其他 Remote 会话混进来。

### 兼容：附加到已经运行的 Remote

如果 Remote 在安装前就已经启动，本工具无法重新接管它现有控制台的 stdout，所以会读取 Desktop Commander 自己的共享历史：

```text
%USERPROFILE%\.claude-server-commander\tool-history.jsonl
```

这种兼容模式在同时存在多个 Remote 对话时，可能显示其他并发会话的工具记录。下一次从 `remote` 启动即可回到独立流模式。

## 颜色说明

| 状态 | 颜色 | 含义 |
| --- | --- | --- |
| ✓ | 绿色 | 成功、正常完成 |
| • | 青色 | 开始执行、普通信息 |
| ⏳ | 紫色 | 仍在运行、等待 |
| ⚠ | 黄色 | 警告、超时、Git 提示 |
| ✗ | 红色 | 错误 |
| · | 灰色 | 无新输出、RAW 辅助信息 |

## 安全与隐私

Remote Log Explainer 的解释器本身只做本地规则解析。

- 不调用 OpenAI、Claude 或其他云端模型。
- 不上传 Remote 日志。
- 不注入 Desktop Commander 进程。
- 不截获网络流量。
- 不创建 Startup、自启动服务、计划任务或隐藏 watcher。
- 显示前对常见凭据进行脱敏。

为了让原始 `npx ... remote` 自动带起 Monitor，安装程序会对当前 Node 安装目录中的 `npx.ps1` 增加一个**只匹配 Desktop Commander Remote 的入口判断**，并在修改前保存备份：

```text
npx.remote-log-backup.ps1
```

其他 `npx` 命令继续执行 npm 原始逻辑。卸载时会恢复备份。

> Node/npm 更新可能重建 `npx.ps1`。如果更新后自动联动失效，重新执行 `scripts\install.ps1` 即可。

## 更新

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

## 卸载

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.remote-log-explainer\scripts\uninstall.ps1"
```

卸载会：

- 停止本项目的 Monitor
- 恢复备份的 `npx.ps1`
- 删除本项目创建的 `remote.cmd`
- 删除 `%USERPROFILE%\.remote-log-explainer`

源码仓库不会被删除。

## 开发与测试

```powershell
python -m py_compile .\src\remote_log.py .\src\remote_runner.py
python -m unittest discover -s tests -v
```

当前测试：6 项单元测试。

项目还提供 GitHub Actions，在 Windows 环境执行 Python 编译、单元测试和 PowerShell 语法检查。

## 项目结构

```text
remote-log-explainer/
├─ src/
│  ├─ remote_log.py
│  └─ remote_runner.py
├─ scripts/
│  ├─ install.ps1
│  ├─ uninstall.ps1
│  ├─ remote-with-monitor.ps1
│  ├─ run-remote.ps1
│  ├─ attach-monitor.ps1
│  ├─ start-monitor.ps1
│  ├─ start-stream-monitor.ps1
│  ├─ console-style.ps1
│  ├─ install-command-hooks.ps1
│  └─ uninstall-command-hooks.ps1
├─ tests/
├─ docs/
│  └─ USAGE.zh-CN.md
└─ VERSION
```

## 已知限制

- 当前主要面向 Windows。
- 原始 `npx ... remote` 自动联动入口目前针对 PowerShell 的 `npx.ps1`。
- 已经运行中的旧 Remote 只能使用共享 history 兼容模式。
- 规则未识别的特殊日志目前不会调用模型猜测，只保留 RAW 查看能力。

## 版本记录

见 [CHANGELOG.md](CHANGELOG.md)。
