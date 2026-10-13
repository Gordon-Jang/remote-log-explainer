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

或者显式指定版本：

```powershell
npx --yes @wonderwhy-er/desktop-commander@0.2.52 remote
```

PowerShell hook 会识别 Desktop Commander 的 `remote` 启动，不要求固定版本，也允许带 `--yes` / `-y`。

进入本项目启动器后，内部统一使用：

```text
npx --yes <你指定的 Desktop Commander package spec> remote
```

因此当 npm 缓存失效、Desktop Commander 发布新版本或本机首次下载新版本时，不会卡在 `Need to install the following packages... Ok to proceed?` 这类交互确认上。

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
- `L`：检查最近一次捕获到的文件/文件夹占用
- `K`：从最近一次占用列表中选择进程并终止；执行前会再次确认
- `C`：清屏
- `Q`：退出 Monitor

RAW 模式用于查看被简化之前的 Remote 原始行或 JSON。

## 文件 / 文件夹占用定位

手动检查任意路径：

```powershell
lockwho "C:\path\to\file-or-folder"
```

文件检查会优先调用 Windows Restart Manager；目录检查会调用安装时验证过 Microsoft 数字签名的 Sysinternals Handle，因此既能看到直接打开的目录句柄，也能看到目录内部文件对应的占用。

查看后可以终止指定进程：

```powershell
lockwho "C:\path\to\file-or-folder" --kill 12345
```

默认还会询问一次确认。只有你明确需要脚本化非交互执行时才使用：

```powershell
lockwho "C:\path\to\file-or-folder" --kill 12345 --yes
```

为了避免误操作，关键 Windows 系统进程会被拒绝终止。其他进程在终止前会提示“未保存数据可能丢失”。

### Monitor 自动捕获

当 Remote 工具输出包含 `WinError 32`、`sharing violation`、`being used by another process`、中文“另一个进程正在使用”等典型占用错误，而且能从工具参数或错误文本提取到实际路径时，Monitor 会显示：

```text
检测到文件/目录占用：C:\work\project\data.db
按 L 查看占用进程；查看后按 K 可选择终止进程。
```

这里的“自动捕获”只针对**经过 Remote 日志的错误**。Windows Explorer、Office 或其他桌面程序自己弹出的“文件正在使用”窗口不会被后台监听；遇到这种情况直接把弹窗里的路径交给 `lockwho` 即可。

### Sysinternals Handle

安装器会从 Microsoft 官方地址下载 Handle，并要求 `handle64.exe` 的 Authenticode 签名状态为 Valid 且签名者为 Microsoft Corporation 后才安装。仓库不包含微软二进制文件；下载后的 EULA 会一并保存在运行目录。

如果下载失败，单文件检查仍可使用 Windows Restart Manager；目录扫描会退回本地兼容扫描，但在句柄很多的电脑上速度会更慢。

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

## 11. 控制台背景与滚动

Remote 和 Monitor 现在会优先在 Windows Terminal 中打开。

原因是经典 Windows 控制台（conhost）使用固定高度的屏幕缓冲区，即使没有真实输出，也可能存在大量空白缓冲行，看起来像“还能一直滚到纯背景”。这些空白并不是历史日志。

Windows Terminal 使用动态滚动历史：只有真正产生的输出才进入 scrollback，因此不会为了预分配缓冲区而出现大段空白。

当前行为：

- 黑色背景
- 灰色普通文字
- 状态行继续使用绿色 / 青色 / 紫色 / 黄色 / 红色
- 不人为限制历史长度
- 不修改 BufferSize
- 不使用 Clear-Host 制造额外空白
- Windows Terminal 不可用时才回退到经典控制台

历史长度仍由 Windows Terminal 自己的设置管理，本项目不截断历史。

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
