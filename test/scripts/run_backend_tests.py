"""Run backend unit tests and persist a protocol report for school documentation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_DIR = ROOT / "test" / "protocols"
PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)


def _git_head_short() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return completed.stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    timestamp = datetime.now(timezone.utc)
    timestamp_iso = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    date_stamp = timestamp.strftime("%Y-%m-%d")

    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "test",
        "-p",
        "test_*.py",
        "-v",
    ]

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    report = "\n".join(
        [
            "# Backend Test Protocol",
            "",
            f"- Generated: {timestamp_iso}",
            f"- Commit: `{_git_head_short()}`",
            f"- Command: `{' '.join(command)}`",
            f"- Exit Code: `{completed.returncode}`",
            "",
            "## Stdout",
            "```text",
            completed.stdout.rstrip() or "<no stdout>",
            "```",
            "",
            "## Stderr",
            "```text",
            completed.stderr.rstrip() or "<no stderr>",
            "```",
            "",
        ]
    )

    latest_path = PROTOCOL_DIR / "backend_test_protocol_latest.md"
    dated_path = PROTOCOL_DIR / f"backend_test_protocol_{date_stamp}.md"
    latest_path.write_text(report + "\n", encoding="utf-8")
    dated_path.write_text(report + "\n", encoding="utf-8")

    print(f"Saved latest protocol: {latest_path}")
    print(f"Saved dated protocol:  {dated_path}")
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
