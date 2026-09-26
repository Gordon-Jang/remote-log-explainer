from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def write_meta(path: Path | None, **values: object) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    values["updatedAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Desktop Commander Remote and tee its console output.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--meta", type=Path)
    args = parser.parse_args()

    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text("", encoding="utf-8")

    command = [
        "cmd.exe",
        "/d",
        "/c",
        "npx.cmd",
        "@wonderwhy-er/desktop-commander@latest",
        "remote",
    ]

    proc = subprocess.Popen(
        command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    write_meta(
        args.meta,
        runnerPid=os.getpid(),
        remotePid=proc.pid,
        logPath=str(args.log),
        running=True,
    )

    exit_code = 1
    try:
        assert proc.stdout is not None
        with args.log.open("a", encoding="utf-8", buffering=1) as log:
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                log.write(line)
                log.flush()
            exit_code = proc.wait()
            marker = f"__REMOTE_LOG_EXPLAINER_SESSION_END__ exit={exit_code}\n"
            sys.stdout.write(marker)
            sys.stdout.flush()
            log.write(marker)
            log.flush()
    except KeyboardInterrupt:
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.terminate()
        exit_code = proc.returncode if proc.returncode is not None else 130
    finally:
        write_meta(
            args.meta,
            runnerPid=os.getpid(),
            remotePid=proc.pid,
            logPath=str(args.log),
            running=False,
            exitCode=exit_code,
        )
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
