from __future__ import annotations

import argparse
import csv
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

if os.name != "nt":
    raise RuntimeError("lock_inspector is Windows-only")

ntdll = ctypes.WinDLL("ntdll")
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
rstrtmgr = ctypes.WinDLL("Rstrtmgr")

SYSTEM_EXTENDED_HANDLE_INFORMATION = 64
CCH_RM_SESSION_KEY = 32
CCH_RM_MAX_APP_NAME = 255
CCH_RM_MAX_SVC_NAME = 63
ERROR_MORE_DATA = 234
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
PROCESS_DUP_HANDLE = 0x0040
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
DUPLICATE_SAME_ACCESS = 0x00000002
FILE_TYPE_DISK = 0x0001
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

PROTECTED_PROCESS_NAMES = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "winlogon.exe", "fontdrvhost.exe", "svchost.exe",
}


class SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX(ctypes.Structure):
    _fields_ = [
        ("Object", ctypes.c_void_p),
        ("UniqueProcessId", ctypes.c_size_t),
        ("HandleValue", ctypes.c_size_t),
        ("GrantedAccess", wintypes.ULONG),
        ("CreatorBackTraceIndex", wintypes.USHORT),
        ("ObjectTypeIndex", wintypes.USHORT),
        ("HandleAttributes", wintypes.ULONG),
        ("Reserved", wintypes.ULONG),
    ]


class RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [
        ("dwProcessId", wintypes.DWORD),
        ("ProcessStartTime", wintypes.FILETIME),
    ]


class RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [
        ("Process", RM_UNIQUE_PROCESS),
        ("strAppName", wintypes.WCHAR * (CCH_RM_MAX_APP_NAME + 1)),
        ("strServiceShortName", wintypes.WCHAR * (CCH_RM_MAX_SVC_NAME + 1)),
        ("ApplicationType", wintypes.DWORD),
        ("AppStatus", wintypes.ULONG),
        ("TSSessionId", wintypes.DWORD),
        ("bRestartable", wintypes.BOOL),
    ]


ntdll.NtQuerySystemInformation.argtypes = [
    wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)
]
ntdll.NtQuerySystemInformation.restype = ctypes.c_long
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.DuplicateHandle.argtypes = [
    wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE,
    ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, wintypes.BOOL, wintypes.DWORD
]
kernel32.DuplicateHandle.restype = wintypes.BOOL
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.GetCurrentProcessId.restype = wintypes.DWORD
kernel32.GetFileType.argtypes = [wintypes.HANDLE]
kernel32.GetFileType.restype = wintypes.DWORD
kernel32.GetFinalPathNameByHandleW.argtypes = [
    wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD
]
kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
]
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel32.TerminateProcess.restype = wintypes.BOOL
kernel32.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
kernel32.ProcessIdToSessionId.restype = wintypes.BOOL

rstrtmgr.RmStartSession.argtypes = [
    ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, wintypes.LPWSTR
]
rstrtmgr.RmStartSession.restype = wintypes.DWORD
rstrtmgr.RmRegisterResources.argtypes = [
    wintypes.DWORD, wintypes.UINT, ctypes.POINTER(wintypes.LPCWSTR),
    wintypes.UINT, ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p
]
rstrtmgr.RmRegisterResources.restype = wintypes.DWORD
rstrtmgr.RmGetList.argtypes = [
    wintypes.DWORD, ctypes.POINTER(wintypes.UINT), ctypes.POINTER(wintypes.UINT),
    ctypes.POINTER(RM_PROCESS_INFO), ctypes.POINTER(wintypes.DWORD)
]
rstrtmgr.RmGetList.restype = wintypes.DWORD
rstrtmgr.RmEndSession.argtypes = [wintypes.DWORD]
rstrtmgr.RmEndSession.restype = wintypes.DWORD
def _ntstatus_u32(value: int) -> int:
    return ctypes.c_ulong(value).value


def _query_system_handles() -> tuple[ctypes.Array[Any], int]:
    size = 1 << 20
    while True:
        buffer = ctypes.create_string_buffer(size)
        needed = wintypes.ULONG(0)
        status = ntdll.NtQuerySystemInformation(
            SYSTEM_EXTENDED_HANDLE_INFORMATION,
            buffer,
            size,
            ctypes.byref(needed),
        )
        if _ntstatus_u32(status) == STATUS_INFO_LENGTH_MISMATCH:
            size = max(size * 2, int(needed.value) + 65536)
            continue
        if status != 0:
            raise OSError(f"NtQuerySystemInformation failed: 0x{_ntstatus_u32(status):08X}")
        count = ctypes.c_size_t.from_buffer_copy(buffer.raw[: ctypes.sizeof(ctypes.c_size_t)]).value
        return buffer, int(count)


def _iter_entries(buffer: ctypes.Array[Any], count: int):
    offset = ctypes.sizeof(ctypes.c_size_t) * 2
    entry_size = ctypes.sizeof(SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX)
    for i in range(count):
        start = offset + i * entry_size
        if start + entry_size > len(buffer):
            break
        yield SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX.from_buffer_copy(buffer, start)


def _normalize_path(path: str) -> str:
    p = path.strip()
    if p.startswith("\\\\?\\UNC\\"):
        p = "\\\\" + p[8:]
    elif p.startswith("\\\\?\\"):
        p = p[4:]
    try:
        p = os.path.abspath(p)
    except Exception:
        pass
    p = os.path.normpath(p)
    return os.path.normcase(p)


def _handle_path(handle: int) -> str | None:
    if kernel32.GetFileType(handle) != FILE_TYPE_DISK:
        return None
    capacity = 1024
    while capacity <= 32768:
        buf = ctypes.create_unicode_buffer(capacity)
        length = kernel32.GetFinalPathNameByHandleW(handle, buf, capacity, 0)
        if length == 0:
            return None
        if length < capacity:
            return buf.value
        capacity = int(length) + 1
    return None


def _process_image(process_handle: int) -> str:
    capacity = wintypes.DWORD(32768)
    buf = ctypes.create_unicode_buffer(capacity.value)
    if kernel32.QueryFullProcessImageNameW(process_handle, 0, buf, ctypes.byref(capacity)):
        return buf.value
    return ""


def _probe_file_type_index(entries: list[SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX]) -> int | None:
    probe_path = os.environ.get("SystemRoot", r"C:\Windows")
    h = kernel32.CreateFileW(
        probe_path,
        0,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    if not h or h == INVALID_HANDLE_VALUE:
        return None
    try:
        pid = int(kernel32.GetCurrentProcessId())
        hv = int(ctypes.cast(h, ctypes.c_void_p).value or 0)
        for entry in entries:
            if int(entry.UniqueProcessId) == pid and int(entry.HandleValue) == hv:
                return int(entry.ObjectTypeIndex)
    finally:
        kernel32.CloseHandle(h)
    return None
def _session_id(pid: int) -> int | None:
    value = wintypes.DWORD(0)
    if kernel32.ProcessIdToSessionId(int(pid), ctypes.byref(value)):
        return int(value.value)
    return None


def _restart_manager_processes(path: str) -> list[dict[str, Any]]:
    session = wintypes.DWORD(0)
    key = ctypes.create_unicode_buffer(CCH_RM_SESSION_KEY + 1)
    rc = rstrtmgr.RmStartSession(ctypes.byref(session), 0, key)
    if rc != 0:
        return []
    try:
        resources = (wintypes.LPCWSTR * 1)(path)
        rc = rstrtmgr.RmRegisterResources(session, 1, resources, 0, None, 0, None)
        if rc != 0:
            return []

        needed = wintypes.UINT(0)
        count = wintypes.UINT(0)
        reboot = wintypes.DWORD(0)
        rc = rstrtmgr.RmGetList(
            session, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reboot)
        )
        if rc == 0 or needed.value == 0:
            return []
        if rc != ERROR_MORE_DATA:
            return []

        infos = (RM_PROCESS_INFO * needed.value)()
        count = wintypes.UINT(needed.value)
        rc = rstrtmgr.RmGetList(
            session, ctypes.byref(needed), ctypes.byref(count), infos, ctypes.byref(reboot)
        )
        if rc != 0:
            return []

        results: list[dict[str, Any]] = []
        for i in range(count.value):
            pid = int(infos[i].Process.dwProcessId)
            process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            image = ""
            if process:
                try:
                    image = _process_image(process)
                finally:
                    kernel32.CloseHandle(process)
            results.append(
                {
                    "pid": pid,
                    "name": os.path.basename(image) if image else infos[i].strAppName or f"PID {pid}",
                    "image": image,
                    "paths": [path],
                    "source": "restart-manager",
                }
            )
        return results
    finally:
        rstrtmgr.RmEndSession(session)


def _find_handle_exe() -> str | None:
    candidates = [
        Path.home() / ".remote-log-explainer" / "tools" / "handle64.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "remote-log-explainer" / "tools" / "handle64.exe",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return str(candidate)
    return None


def _sysinternals_handle_processes(path: str) -> list[dict[str, Any]] | None:
    exe = _find_handle_exe()
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "-accepteula", "-nobanner", "-v", path],
            capture_output=True,
            text=True,
            encoding="mbcs",
            errors="replace",
            timeout=12,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    text = proc.stdout or ""
    if "Process,PID,Type,Handle,Name" not in text:
        return None

    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip().startswith("Process,PID,Type,Handle,Name"))
    except StopIteration:
        return []

    results: dict[int, dict[str, Any]] = {}
    for row in csv.reader(lines[start + 1:]):
        if len(row) < 5:
            continue
        name, pid_text, obj_type, handle_value, held_path = [x.strip() for x in row[:5]]
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        image = ""
        if process:
            try:
                image = _process_image(process)
            finally:
                kernel32.CloseHandle(process)
        item = results.setdefault(
            pid,
            {
                "pid": pid,
                "name": os.path.basename(image) if image else name or f"PID {pid}",
                "image": image,
                "paths": [],
                "source": "sysinternals-handle",
            },
        )
        display = held_path if held_path and "?" not in held_path else path
        if display not in item["paths"]:
            item["paths"].append(display)
        item.setdefault("handles", []).append(handle_value)
    return sorted(results.values(), key=lambda x: (x["name"].lower(), x["pid"]))


def find_locking_processes(path: str | os.PathLike[str], *, all_sessions: bool = False) -> list[dict[str, Any]]:
    target_raw = os.path.abspath(os.fspath(path))
    target = _normalize_path(target_raw)
    is_dir = os.path.isdir(target_raw)
    prefix = target.rstrip("\\/") + os.sep

    # Restart Manager is the fast, built-in path for individual files.
    if not is_dir:
        rm_results = _restart_manager_processes(target_raw)
        if rm_results:
            return sorted(rm_results, key=lambda x: (x["name"].lower(), x["pid"]))

    # Directories are best handled by Microsoft's Sysinternals Handle.
    # It can search directory handles and child file handles much faster than
    # walking every system handle from Python. The installer fetches it from
    # download.sysinternals.com and verifies the Microsoft signature.
    handle_results = _sysinternals_handle_processes(target_raw)
    if handle_results is not None:
        return handle_results

    # If the verified Sysinternals helper is unavailable, keep the native
    # scanner as a compatibility fallback. It is slower on machines with many
    # open handles.
    buffer, count = _query_system_handles()
    entries = list(_iter_entries(buffer, count))
    file_type_index = _probe_file_type_index(entries)

    current_process = kernel32.GetCurrentProcess()
    current_session = _session_id(os.getpid())
    process_handles: dict[int, int] = {}
    process_images: dict[int, str] = {}
    process_sessions: dict[int, int | None] = {}
    results: dict[int, dict[str, Any]] = {}

    try:
        for entry in entries:
            if file_type_index is not None and int(entry.ObjectTypeIndex) != file_type_index:
                continue
            pid = int(entry.UniqueProcessId)
            if pid <= 0 or pid == os.getpid():
                continue

            if not all_sessions and current_session is not None:
                if pid not in process_sessions:
                    process_sessions[pid] = _session_id(pid)
                if process_sessions[pid] != current_session:
                    continue

            process = process_handles.get(pid)
            if process is None:
                process = kernel32.OpenProcess(
                    PROCESS_DUP_HANDLE | PROCESS_QUERY_LIMITED_INFORMATION,
                    False,
                    pid,
                )
                process_handles[pid] = int(process or 0)
                if not process:
                    continue
                process_images[pid] = _process_image(process)

            dup = wintypes.HANDLE()
            if not kernel32.DuplicateHandle(
                process,
                wintypes.HANDLE(int(entry.HandleValue)),
                current_process,
                ctypes.byref(dup),
                0,
                False,
                DUPLICATE_SAME_ACCESS,
            ):
                continue
            try:
                raw_path = _handle_path(dup)
            finally:
                kernel32.CloseHandle(dup)
            if not raw_path:
                continue

            normalized = _normalize_path(raw_path)
            matched = normalized == target or (is_dir and normalized.startswith(prefix))
            if not matched:
                continue

            image = process_images.get(pid, "")
            name = os.path.basename(image) if image else f"PID {pid}"
            item = results.setdefault(
                pid,
                {
                    "pid": pid,
                    "name": name,
                    "image": image,
                    "paths": [],
                    "source": "handle-scan",
                },
            )
            display_path = raw_path[4:] if raw_path.startswith("\\\\?\\") else raw_path
            if display_path not in item["paths"]:
                item["paths"].append(display_path)
    finally:
        for handle in process_handles.values():
            if handle:
                kernel32.CloseHandle(handle)

    return sorted(results.values(), key=lambda x: (x["name"].lower(), x["pid"]))


def terminate_process(pid: int, *, allow_system: bool = False) -> tuple[bool, str]:
    if pid in {0, 4, os.getpid()}:
        return False, "拒绝终止系统/当前进程。"

    process = kernel32.OpenProcess(
        PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        int(pid),
    )
    if not process:
        return False, f"无法打开 PID {pid}，可能需要管理员权限。"
    try:
        image = _process_image(process)
        name = os.path.basename(image).lower() if image else ""
        if not allow_system and name in PROTECTED_PROCESS_NAMES:
            return False, f"拒绝终止受保护系统进程：{name}。"
        if not kernel32.TerminateProcess(process, 1):
            return False, f"终止 PID {pid} 失败，WinError={ctypes.get_last_error()}。"
        return True, f"已终止 {os.path.basename(image) or '进程'} (PID {pid})。"
    finally:
        kernel32.CloseHandle(process)
def print_results(path: str, results: list[dict[str, Any]], *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps({"path": path, "processes": results}, ensure_ascii=False, indent=2))
        return
    print(f"占用检查：{path}")
    if not results:
        print("未发现当前持有该文件/目录句柄的普通进程。")
        return
    for i, item in enumerate(results, 1):
        print(f"[{i}] {item['name']}  PID {item['pid']}")
        if item.get("image"):
            print(f"    程序：{item['image']}")
        for held in item.get("paths", [])[:5]:
            print(f"    占用：{held}")
        extra = len(item.get("paths", [])) - 5
        if extra > 0:
            print(f"    另有 {extra} 个匹配句柄")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find Windows processes locking a file or folder.")
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--kill", type=int, metavar="PID")
    parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation for --kill.")
    parser.add_argument(
        "--all-sessions",
        action="store_true",
        help="Deep scan service/other Windows sessions too; slower and may require elevation.",
    )
    args = parser.parse_args()

    target = os.path.abspath(os.path.expandvars(os.path.expanduser(args.path)))
    if not os.path.exists(target):
        print(f"路径不存在：{target}", file=sys.stderr)
        return 2

    started = time.perf_counter()
    results = find_locking_processes(target, all_sessions=args.all_sessions)
    print_results(target, results, as_json=args.json)
    if not args.json:
        print(f"扫描耗时：{time.perf_counter() - started:.2f}s")

    if args.kill is None:
        return 0
    candidates = {int(x["pid"]): x for x in results}
    if args.kill not in candidates:
        print(f"PID {args.kill} 不在本次占用列表中，未终止。", file=sys.stderr)
        return 3
    item = candidates[args.kill]
    if not args.yes:
        answer = input(f"确认终止 {item['name']} (PID {args.kill})？[y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("已取消。")
            return 0
    ok, message = terminate_process(args.kill)
    print(message)
    return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
