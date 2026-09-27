# Remote Log Explainer 使用指南

本文档面向日常使用和故障排查。项目默认不使用大模型，所有日志解释都在本机完成。

## 1. 安装前检查

确认下面命令均可用：

```powershell
python --version
node --version
npx --version
```

并确认 Desktop Commander Remote 原始命令能够启动：

```powershell
npx @wonderwhy-er/desktop-commander@latest remote
```

如果原始 Remote 本身不能连接，请先解决 Desktop Commander、Node、网络或认证问题；本项目不会修复 Remote 本身的连接故障。

## 2. 安装

```powershell
git clone https://github.com/Gordon-Jang/remote-log-explainer.git
cd remote-log-explainer
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

安装会做四件事：

1. 把运行文件复制到 `%USERPROFILE%\.remote-log-explainer`。
2. 在 Node/npm 的命令目录旁创建 `remote.cmd`。
3. 对 PowerShell 使用的 `npx.ps1` 增加 Desktop Commander Remote 的精确匹配入口。
4. 在修改 `npx.ps1` 前保存 `npx.remote-log-backup.ps1`。

安装不会写 Windows Startup，不会创建计划任务，也不会启动隐藏 watcher。

## 3. 推荐启动方式

日常直接输入：

```powershell
remote
```

如果当前没有 Remote，会打开：

```text
窗口 1：Desktop Commander Remote
窗口 2：Remote Monitor
```

Remote 窗口保留原始输出，Monitor 窗口给出简化中文解释。

## 4. 保留原始命令

你也可以继续输入：

```powershell
npx @wonderwhy-er/desktop-commander@latest remote
```

在 PowerShell 中，这条命令会被精确识别，并进入和 `remote` 相同的启动流程。

匹配只针对：

```text
@wonderwhy-er/desktop-commander@latest remote
```

普通命令例如：

```powershell
npx --version
npx vite
npx eslint .
```

仍交给原始 npm/npx 处理。

## 5. Remote 已经运行时

再次输入：

```powershell
remote
```

或：

```powershell
npx @wonderwhy-er/desktop-commander@latest remote
```

不会再开第二个 Remote。

行为是：

```text
检测到 Remote 已运行
  ↓
检测 Monitor
  ↓
Monitor 不存在 → 打开
Monitor 已存在 → 复用
```

## 6. Monitor 输出怎么读

### 普通信息

```text
• 开始 · 读取文件
```

表示 Remote 收到一个工具调用。

### 成功

```text
✓ 进程已完成 · PID 12345
```

表示对应进程已经正常退出。

### 仍在运行

```text
⏳ 命令仍在运行 · PID 35776
```

这并不等于卡死。Desktop Commander 有时会把“当前无输出/等待输入”标记成等待状态。

### 警告

```text
⚠ 网络连接正在重试
```

或：

```text
⚠ Git 换行符提示（LF/CRLF）
```

黄色代表需要注意，但不一定导致任务失败。

### 错误

```text
✗ Remote 报错
```

红色代表明确错误或非 0 退出状态。

## 7. 快捷键

Monitor 窗口中：

- `R`：切换 RAW 模式
- `C`：清屏
- `Q`：退出 Monitor

RAW 模式用于查看被简化之前的 Remote 原始行或 JSON。

## 8. 会话隔离

### 新 Remote：独立日志

由本工具启动的新 Remote 会为每次会话创建独立日志：

```text
%USERPROFILE%\.remote-log-explainer\runtime\streams\
```

Monitor 只读取这一份流，所以不同 Remote 会话不会互相混入。

### 已经运行的 Remote：共享历史兼容模式

如果 Remote 在安装本工具之前已经启动，无法从外部重新接管它现有控制台的 stdout。

此时 Monitor 会读取：

```text
%USERPROFILE%\.claude-server-commander\tool-history.jsonl
```

这个文件由 Desktop Commander 自己维护，是共享历史。如果多个对话同时调用同一个 Remote，兼容模式可能看到其他会话的记录。

解决方法：结束旧 Remote，之后使用 `remote` 重新启动。

## 9. 日志与隐私

解释器不会把日志发送给大模型。

显示前会处理常见形式的：

- Bearer Authorization
- API key
- token
- password
- secret
- OpenAI 风格 `sk-...`
- GitHub token 风格前缀

这不是完整 DLP 系统。不要把 RAW 日志公开发布，除非你已经确认没有敏感内容。

## 10. Node/npm 更新后的处理

Node 或 npm 更新可能重新生成：

```text
npx.ps1
```

如果发现：

```powershell
npx @wonderwhy-er/desktop-commander@latest remote
```

不再自动打开 Monitor，但 `remote` 仍然正常，重新运行：

```powershell
cd <仓库目录>
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

即可重新安装入口。

## 11. 控制台背景与滚动历史

Remote 和 Monitor 默认都会设置为：

- 黑色背景
- 灰色普通文字
- 状态行继续使用绿色 / 青色 / 紫色 / 黄色 / 红色
- 控制台缓冲区最多保留 1000 行

当输出超过 1000 行后，最旧的控制台内容会被自动丢弃，因此窗口不会再无限向下积累历史。

这个限制只影响终端可滚动历史，不影响当前 Remote 任务本身。

## 12. Monitor 没有颜色

正常颜色：

- 绿色：成功
- 青色：信息
- 紫色：运行中
- 黄色：警告
- 红色：错误
- 灰色：辅助

Windows 上程序会优先开启 VT/ANSI 模式；如果控制台不支持，会退回 Windows Console API。

如果你看到类似：

```text
[92m
[0m
```

说明终端把 ANSI 转义码当成普通文本。请确认你使用的是当前版本，并重新运行安装脚本。

## 13. 手动附加 Monitor

如果你明确希望给一个已经运行的 Remote 开监控：

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.remote-log-explainer\scripts\attach-monitor.ps1"
```

该模式属于共享 history 兼容模式。

## 14. 手动启动完整流程

不经过 `remote` 命令也可以：

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.remote-log-explainer\scripts\remote-with-monitor.ps1"
```

## 15. 更新

```powershell
cd <仓库目录>
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

## 16. 卸载

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.remote-log-explainer\scripts\uninstall.ps1"
```

卸载脚本会恢复原始 `npx.ps1` 备份并删除本项目创建的 `remote.cmd`。

如果源码是通过 Git clone 得到的，源码目录不会被卸载脚本删除。

## 17. 开发测试

```powershell
python -m py_compile .\src\remote_log.py .\src\remote_runner.py
python -m unittest discover -s tests -v
```

PowerShell 语法可使用：

```powershell
$errors = @()
Get-ChildItem .\scripts\*.ps1 | ForEach-Object {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $_.FullName,
        [ref]$tokens,
        [ref]$parseErrors
    ) | Out-Null
    $errors += $parseErrors
}
$errors
```

没有输出即表示没有 PowerShell 解析错误。
