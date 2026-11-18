"""CI guard: no books, scans, secrets, or large binaries in the repository (docs/security.md section 2).

Checks every file git would track (tracked + untracked, minus ignored). Exit code 1 on any finding.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BINARY_BYTES = 1_000_000
BLOCKED_SUFFIXES = {".pdf", ".djvu", ".epub", ".mobi", ".tif", ".tiff", ".cbz"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".zip", ".gz", ".7z", ".bin"}
BLOCKED_NAMES = {".env"}


def tracked_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return [ROOT / name for name in output.decode("utf-8").split("\0") if name]


def find_problems(files: list[Path]) -> list[str]:
    problems = []
    for path in files:
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if path.name in BLOCKED_NAMES or (
            path.name.startswith(".env.") and path.name != ".env.example"
        ):
            problems.append(f"{relative}: environment file must not be committed")
        elif path.suffix.lower() in BLOCKED_SUFFIXES:
            problems.append(f"{relative}: book/scan format must not be committed")
        elif path.suffix.lower() in BINARY_SUFFIXES and path.stat().st_size > MAX_BINARY_BYTES:
            problems.append(f"{relative}: binary larger than {MAX_BINARY_BYTES} bytes")
    return problems


def main() -> int:
    problems = find_problems(tracked_files())
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("repository file check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
