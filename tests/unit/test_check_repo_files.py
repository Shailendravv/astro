"""The repository file guard (scripts/check_repo_files.py) flags books, env files and big binaries."""

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_repo_files", ROOT / "scripts" / "check_repo_files.py"
)
assert spec is not None
assert spec.loader is not None
guard: Any = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_flags_pdf_env_and_large_binary(tmp_path: Path) -> None:
    guard.ROOT = tmp_path
    (tmp_path / "book.pdf").write_bytes(b"x")
    (tmp_path / ".env").write_text("A=1")
    (tmp_path / "scan.png").write_bytes(b"x" * (guard.MAX_BINARY_BYTES + 1))
    problems = guard.find_problems(list(tmp_path.iterdir()))
    assert len(problems) == 3


def test_allows_env_example_and_small_images(tmp_path: Path) -> None:
    guard.ROOT = tmp_path
    (tmp_path / ".env.example").write_text("A=")
    (tmp_path / "icon.png").write_bytes(b"x" * 10)
    assert guard.find_problems(list(tmp_path.iterdir())) == []


def test_the_real_repository_is_clean() -> None:
    guard.ROOT = ROOT
    assert guard.find_problems(guard.tracked_files()) == []
