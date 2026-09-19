"""Audit tracked repository content for accidentally committed credentials.

The audit intentionally reads only Git-tracked files. Local dotenv files and
injected CI environment variables are never treated as repository content.
Secret values are used only for in-memory comparison and are never printed.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from dotenv import dotenv_values


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_VARS = {
    "DATABASE_URL",
    "GEMINI_API_KEY",
    "MOSS_PROJECT_KEY",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
}
EXCLUDED_DIRS = {
    ".git",
    ".next",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "scratch",
    "media",
}
EXCLUDED_FILES = {".env", ".env.local", ".env.example"}
JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")


def _tracked_files() -> Iterable[Path]:
    """Return tracked files, with a filesystem fallback for source archives."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        )
        for name in result.stdout.decode("utf-8", errors="ignore").split("\0"):
            if name:
                yield REPOSITORY_ROOT / name
        return
    except (OSError, subprocess.CalledProcessError):
        pass

    for path in REPOSITORY_ROOT.rglob("*"):
        if path.is_file():
            yield path


def _local_secret_values() -> set[str]:
    values: set[str] = set()
    for env_file in (
        REPOSITORY_ROOT / ".env",
        REPOSITORY_ROOT / ".env.local",
        REPOSITORY_ROOT / "frontend" / ".env.local",
    ):
        if not env_file.exists():
            continue
        for key, value in dotenv_values(env_file).items():
            if key in SENSITIVE_VARS and value and len(value.strip()) > 8:
                values.add(value.strip())
    return values


def _is_excluded(path: Path) -> bool:
    relative = path.relative_to(REPOSITORY_ROOT)
    return (
        path.name in EXCLUDED_FILES
        or any(part in EXCLUDED_DIRS for part in relative.parts)
        or path.suffix.lower() in {".pyc", ".png", ".webp", ".jpg", ".jpeg", ".gif", ".log"}
    )


def main() -> int:
    secret_values = _local_secret_values()
    violations: set[str] = set()

    for path in _tracked_files():
        if not path.exists() or _is_excluded(path):
            continue
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        for line_number, line in enumerate(lines, start=1):
            if any(secret in line for secret in secret_values):
                violations.add(f"secret value match: {relative}:{line_number}")
            if JWT_PATTERN.search(line) and not relative.startswith("tests/"):
                violations.add(f"JWT pattern match: {relative}:{line_number}")

    print("PRE-DEPLOYMENT REPOSITORY SECURITY AUDIT")
    if violations:
        print("secret exposure found = true")
        for violation in sorted(violations):
            print(f"  - {violation}")
        return 1

    print("secret exposure found = false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
