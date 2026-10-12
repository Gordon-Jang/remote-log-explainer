from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_PACKAGE_SPEC = "@wonderwhy-er/desktop-commander@latest"


def write_meta(path: Path | None, **values: object) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    values["updatedAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")


def build_command(package_spec: str) -> list[str]:
    if not package_spec.startswith("@wonderwhy-er/desktop-commander"):
        raise ValueError(f"Unsupported package spec: {package_spec}")
    return [
        "cmd.exe",
        "/d",
        "/c",
        "npx.cmd",
        "--yes",
        package_spec,
        "remote",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Desktop Commander Remote and tee its console output.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--meta", type=Path)
    parser.add_argument(
        "--package-spec",
        default=os.environ.get("DESKTOP_COMMANDER_PACKAGE", DEFAULT_PACKAGE_SPEC),
        help="Desktop Commander npm package spec, e.g. @wonderwhy-er/desktop-commander@0.2.52",
    )
    args = parser.parse_args()

    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text("", encoding="utf-8")

    command = build_command(args.package_spec)

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
        packageSpec=args.package_spec,
        command=command,
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
            packageSpec=args.package_spec,
            command=command,
            logPath=str(args.log),
            running=False,
            exitCode=exit_code,
        )
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
