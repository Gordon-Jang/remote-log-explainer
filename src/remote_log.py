from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

HISTORY = Path.home() / ".claude-server-commander" / "tool-history.jsonl"
ANSI = {
    "ok": "\033[92m",
    "info": "\033[96m",
    "wait": "\033[95m",
    "warn": "\033[93m",
    "error": "\033[91m",
    "dim": "\033[90m",
    "reset": "\033[0m",
}
ICONS = {"ok": "✓", "info": "•", "wait": "⏳", "warn": "⚠", "error": "✗", "dim": "·"}
RAW_MODE = False
SECRET_PATTERNS = [
    (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s\"']+"), r"\1***"),
    (re.compile(r"(?i)((?:api[_-]?key|token|password|secret)\s*[:=]\s*)[^\s,;\"']+"), r"\1***"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "***"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "***"),
]

def redact(text: str) -> str:
    text = str(text)
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

def compact(text: Any, limit: int = 130) -> str:
    s = redact(str(text or ""))
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > limit:
        return s[: limit - 1] + "…"
    return s

def output_text(record: Dict[str, Any]) -> str:
    out = record.get("output") or {}
    pieces: List[str] = []
    for part in out.get("content") or []:
        if isinstance(part, dict) and part.get("type") == "text":
            pieces.append(str(part.get("text") or ""))
    return "\n".join(pieces)
def display_time(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "--:--:--"

def file_label(value: Any) -> str:
    if not value:
        return "(未提供路径)"
    p = str(value).replace("/", "\\")
    parts = [x for x in p.split("\\") if x]
    if len(parts) <= 3:
        return compact(p, 100)
    return compact("\\".join(parts[-3:]), 100)

def parse_pid(text: str) -> str:
    m = re.search(r"PID\s+(\d+)", text, flags=re.I)
    return m.group(1) if m else ""

def process_level(text: str) -> str:
    low = text.lower()
    m = re.search(r"exit code\s+(-?\d+)", low)
    if m:
        return "ok" if m.group(1) == "0" else "error"
    if "request timed out" in low or "timed out" in low:
        return "warn"
    if "waiting for input" in low:
        return "wait"
    if low.lstrip().startswith(("error:", "failed:", "❌")):
        return "error"
    return "ok"
def classify(record: Dict[str, Any]) -> Tuple[str, str, List[str]]:
    tool = str(record.get("toolName") or "unknown")
    args = record.get("arguments") or {}
    out = output_text(record)
    details: List[str] = []
    level = "ok"

    if tool == "read_file":
        title = "读取文件"
        details.append(file_label(args.get("path")))
        m = re.search(r"\[Reading ([^\]]+)\]", out)
        if m:
            details.append(compact(m.group(1), 100))
    elif tool == "read_multiple_files":
        title = "批量读取文件"
        paths = args.get("paths") or []
        details.append(f"{len(paths)} 个文件")
    elif tool == "write_file":
        title = "写入文件"
        details.append(file_label(args.get("path")))
        details.append(f"模式：{args.get('mode', 'rewrite')}")
    elif tool == "edit_block":
        title = "修改文件"
        details.append(file_label(args.get("file_path")))
        details.append(f"预计替换：{args.get('expected_replacements', 1)} 处")
    elif tool == "list_directory":
        title = "查看目录"
        details.append(file_label(args.get("path")))
    elif tool == "create_directory":
        title = "创建目录"
        details.append(file_label(args.get("path")))
    elif tool == "move_file":
        title = "移动/重命名文件"
        details.extend([file_label(args.get("source")), "→ " + file_label(args.get("destination"))])
    elif tool == "get_file_info":
        title = "读取文件信息"
        details.append(file_label(args.get("path")))
    elif tool == "start_process":
        level = process_level(out)
        pid = parse_pid(out)
        if re.search(r"exit code\s+0", out, flags=re.I):
            title = f"命令执行完成{(' · PID ' + pid) if pid else ''}"
        elif "waiting for input" in out.lower():
            title = f"命令仍在运行{(' · PID ' + pid) if pid else ''}"
            level = "wait"
            details.append("当前工具判断它可能在等待输入；不等于程序卡死")
        else:
            title = f"启动命令{(' · PID ' + pid) if pid else ''}"
        test_count = re.search(r"Ran\s+(\d+)\s+tests?", out)
        if test_count and re.search(r"(?m)^OK\s*$", out):
            details.append(f"测试通过：{test_count.group(1)} 项")
        details.append(compact(args.get("command"), 150))
        if "request timed out" in out.lower():
            details.append("检测到超时；程序可能正在重试或切换传输方式")
        if "falling back from websockets to https transport" in out.lower():
            details.append("WebSocket 超时后已切换 HTTPS 传输")
    elif tool == "read_process_output":
        pid = str(args.get("pid") or "")
        level = process_level(out)
        if re.search(r"exit code\s+0", out, flags=re.I):
            title = f"进程已完成 · PID {pid}"
        elif "waiting for input" in out.lower():
            title = f"进程仍在运行 · PID {pid}"
            level = "wait"
            details.append("当前工具判断它可能在等待输入")
        elif "no output in requested range" in out.lower():
            title = f"暂时没有新输出 · PID {pid}"
            level = "dim"
        else:
            title = f"读取进程输出 · PID {pid}"
        test_count = re.search(r"Ran\s+(\d+)\s+tests?", out)
        if test_count and re.search(r"(?m)^OK\s*$", out):
            details.append(f"测试通过：{test_count.group(1)} 项")
    elif tool == "interact_with_process":
        pid = str(args.get("pid") or "")
        level = process_level(out)
        title = f"向进程发送输入 · PID {pid}"
        details.append(compact(args.get("input"), 120))
    elif tool == "force_terminate":
        level = "warn"
        title = f"强制结束进程 · PID {args.get('pid', '')}"
    elif tool == "list_processes":
        title = "查看运行中的进程"
    elif tool == "list_sessions":
        title = "查看远程终端会话"
    elif tool == "get_config":
        title = "读取 Remote 配置"
    elif tool == "set_config_value":
        level = "warn"
        title = "修改 Remote 配置"
        details.append(f"{args.get('key')} = {compact(args.get('value'), 80)}")
    elif tool == "get_recent_tool_calls":
        title = "读取 Remote 工具历史"
    else:
        title = tool
        if args:
            details.append(compact(json.dumps(args, ensure_ascii=False), 140))

    stripped = out.lstrip()
    if tool not in {"read_file", "read_multiple_files"}:
        if stripped.startswith(("Error:", "Failed:", "❌", "[DENIED]", "[NOT_FOUND]")):
            level = "error"
    if "warning: in the working copy" in out.lower():
        level = "warn"
        details.append("Git 换行符提示（LF/CRLF），通常不影响本次执行")
    return level, title, details[:3]
def colorize(level: str, text: str) -> str:
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return text
    return ANSI.get(level, "") + text + ANSI["reset"]

def render_summary(level: str, title: str, details: Iterable[str], stamp: str | None = None) -> None:
    stamp = stamp or datetime.now().astimezone().strftime("%H:%M:%S")
    icon = ICONS.get(level, "•")
    print(colorize(level, f"{stamp}  {icon} {title}"), flush=True)
    for detail in details:
        if detail:
            print("          " + compact(detail, 170), flush=True)

def render(record: Dict[str, Any], raw: bool = False) -> None:
    level, title, details = classify(record)
    stamp = display_time(str(record.get("timestamp") or ""))
    render_summary(level, title, details, stamp)
    if raw:
        raw_text = redact(json.dumps(record, ensure_ascii=False))
        print(colorize("dim", "          RAW " + compact(raw_text, 900)), flush=True)

def read_recent(path: Path, count: int) -> Iterable[Dict[str, Any]]:
    if count <= 0 or not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]
    records: List[Dict[str, Any]] = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records

def _stream_pending(state: Dict[str, Any], tool: str) -> Dict[str, Any]:
    queues = state.setdefault("pending", {})
    queue = queues.setdefault(tool, [])
    if queue:
        return queue.pop(0)
    return {"tool": tool, "args": {}, "origin": ""}

def _stream_complete(tool: str, result: Dict[str, Any], state: Dict[str, Any]) -> None:
    pending = _stream_pending(state, tool)
    record = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "toolName": tool,
        "arguments": pending.get("args") or {},
        "output": result,
        "duration": 0,
    }
    level, title, details = classify(record)
    if level == "ok":
        title = "完成 · " + title
    origin = str(pending.get("origin") or "")
    if origin:
        details.append("会话：" + origin)
    render_summary(level, title, details)

def parse_stream_line(line: str, state: Dict[str, Any]) -> bool:
    raw = line.rstrip("\r\n")
    if not raw:
        return False

    if raw.startswith("__REMOTE_LOG_EXPLAINER_SESSION_END__"):
        m = re.search(r"exit=(-?\d+)", raw)
        code = int(m.group(1)) if m else 0
        level = "ok" if code == 0 else "error"
        render_summary(level, f"Remote 已结束 · exit {code}", [])
        return True

    awaiting = state.get("awaiting_completion")
    if awaiting:
        try:
            result = json.loads(raw.strip())
        except Exception:
            if RAW_MODE:
                print(colorize("dim", "RAW " + compact(raw, 900)), flush=True)
            return False
        state["awaiting_completion"] = None
        _stream_complete(str(awaiting), result, state)
        return False

    received = re.search(
        r"Received tool call\s+([^:]+):\s+([A-Za-z0-9_]+)\s+(.*?)\s+metadata:\s+(\{.*\})\s*$",
        raw,
    )
    if received:
        call_id, tool, args_text, meta_text = received.groups()
        try:
            args = json.loads(args_text)
        except Exception:
            args = {}
        try:
            metadata = json.loads(meta_text)
        except Exception:
            metadata = {}
        origin = str(metadata.get("origin_instance") or "")
        state.setdefault("pending", {}).setdefault(tool, []).append(
            {"call_id": call_id, "tool": tool, "args": args, "origin": origin}
        )
        record = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "toolName": tool,
            "arguments": args,
            "output": {"content": []},
            "duration": 0,
        }
        _, title, details = classify(record)
        if origin:
            details.append("会话：" + origin)
        render_summary("info", "开始 · " + title, details)
        if RAW_MODE:
            print(colorize("dim", "RAW " + compact(raw, 900)), flush=True)
        return False

    completed = re.search(r"Tool call\s+([A-Za-z0-9_]+)\s+completed:\s*(.*)$", raw)
    if completed:
        tool, payload = completed.groups()
        payload = payload.strip()
        if not payload:
            state["awaiting_completion"] = tool
        else:
            try:
                result = json.loads(payload)
            except Exception:
                result = {"content": [{"type": "text", "text": payload}]}
            _stream_complete(tool, result, state)
        if RAW_MODE:
            print(colorize("dim", "RAW " + compact(raw, 900)), flush=True)
        return False

    low = raw.lower()
    if "reconnecting" in low or "request timed out" in low:
        render_summary("warn", "网络连接正在重试", [raw])
    elif low.startswith(("error", "fatal", "failed")):
        render_summary("error", "Remote 报错", [raw])
    elif low.startswith("warning"):
        render_summary("warn", "Remote 警告", [raw])
    elif RAW_MODE:
        print(colorize("dim", "RAW " + compact(raw, 900)), flush=True)
    return False

def stream_follow(path: Path, status: Path | None) -> int:
    state: Dict[str, Any] = {}
    while not path.exists():
        print(f"等待 Remote 日志：{path}", flush=True)
        time.sleep(0.5)
        if not handle_keys():
            return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        while True:
            if not handle_keys():
                return 0
            line = fh.readline()
            if not line:
                write_status(status, running=True, mode="stream", events=count, logPath=str(path))
                time.sleep(0.2)
                continue
            done = parse_stream_line(line, state)
            count += 1
            write_status(status, running=not done, mode="stream", events=count, logPath=str(path))
            if done:
                time.sleep(2)
                return 0

def pid_alive(pid: int) -> bool:
    if pid <= 0 or os.name != "nt":
        return True
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    return False
def write_status(path: Path | None, **values: Any) -> None:
    if not path:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        current: Dict[str, Any] = {}
        if path.exists():
            current = json.loads(path.read_text(encoding="utf-8"))
        current.update(values)
        current["updatedAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass

def handle_keys() -> bool:
    global RAW_MODE
    if os.name != "nt":
        return True
    try:
        import msvcrt
        if not msvcrt.kbhit():
            return True
        key = msvcrt.getwch().lower()
        if key == "q":
            return False
        if key == "r":
            RAW_MODE = not RAW_MODE
            print(colorize("info", f"RAW 模式：{'开' if RAW_MODE else '关'}"), flush=True)
        elif key == "c":
            os.system("cls")
            banner()
    except Exception:
        pass
    return True

def banner() -> None:
    if sys.stdout.isatty():
        print("\033]0;Remote Monitor\007", end="")
    print("Remote Monitor  ·  规则解释器（0 模型）")
    print("R 原始 JSON   C 清屏   Q 退出")
    print("─" * 62)
def follow(path: Path, replay: int, session_pid: int, status: Path | None) -> int:
    for record in read_recent(path, replay):
        render(record, RAW_MODE)
    while not path.exists():
        print(f"等待日志文件：{path}")
        time.sleep(1)
        if session_pid and not pid_alive(session_pid):
            return 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        fh.seek(0, os.SEEK_END)
        pos = fh.tell()
        count = 0
        while True:
            if not handle_keys():
                return 0
            if session_pid and not pid_alive(session_pid):
                print(colorize("warn", "Remote 已结束，监控窗口即将关闭。"))
                write_status(status, running=False, remotePid=session_pid, events=count)
                time.sleep(3)
                return 0
            try:
                size = path.stat().st_size
                if size < pos:
                    fh.seek(0)
                    pos = 0
            except OSError:
                time.sleep(0.3)
                continue
            line = fh.readline()
            if not line:
                write_status(status, running=True, remotePid=session_pid, events=count)
                time.sleep(0.25)
                continue
            pos = fh.tell()
            try:
                record = json.loads(line)
            except Exception:
                continue
            render(record, RAW_MODE)
            count += 1
            write_status(status, running=True, remotePid=session_pid, events=count,
                         lastTool=record.get("toolName"), lastTimestamp=record.get("timestamp"))
def main() -> int:
    parser = argparse.ArgumentParser(description="Explain Desktop Commander tool logs in plain Chinese.")
    parser.add_argument("--history", type=Path, default=HISTORY)
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--stream-log", type=Path)
    parser.add_argument("--replay", type=int, default=0)
    parser.add_argument("--session-pid", type=int, default=0)
    parser.add_argument("--status", type=Path)
    args = parser.parse_args()

    banner()
    if args.stream_log:
        return stream_follow(args.stream_log, args.status)
    if args.follow:
        return follow(args.history, max(0, args.replay), args.session_pid, args.status)
    records = list(read_recent(args.history, max(1, args.replay or 10)))
    for record in records:
        render(record, RAW_MODE)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
