"""Repository-level guards from CLAUDE.md that can be checked mechanically."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".venv", "node_modules", ".next", "__pycache__", ".mypy_cache", ".ruff_cache"}
SKIP_FILES = {"uv.lock", "package-lock.json", "test_repo_guards.py"}
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".mjs", ".json", ".yaml", ".yml", ".toml", ".ps1"}
MODEL_ID_PATTERN = re.compile(
    r"\b(?:qwen|claude|llama|gpt|opus|sonnet|haiku)[-/._]?[\w./-]*\d", re.I
)


def _code_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if (
            path.is_file()
            and path.suffix in CODE_SUFFIXES
            and path.name not in SKIP_FILES
            and not SKIP_DIRS.intersection(path.relative_to(ROOT).parts)
            and "docs" not in path.relative_to(ROOT).parts[:1]
        ):
            files.append(path)
    return files


def test_no_model_id_is_hard_coded_anywhere_in_code_or_config() -> None:
    """CLAUDE.md rule 11: model IDs live only in the decisions.md register and the local .env."""
    offenders = []
    for path in _code_files():
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            if MODEL_ID_PATTERN.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:100]}")
    assert not offenders, "model-ID-like strings found:\n" + "\n".join(offenders)


def test_env_example_lists_settings_without_values_for_secrets_and_models() -> None:
    values = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    for key in ("POSTGRES_PASSWORD", "GROQ_API_KEY", "RUNTIME_MODEL_ID", "EVAL_JUDGE_MODEL_ID"):
        assert key in values, f"{key} missing from .env.example"
        assert values[key] == "", f"{key} must have no value in .env.example"
    assert not any(key.startswith("ANTHROPIC") for key in values), "no Anthropic setting (D-030)"


def test_tradition_packages_exist() -> None:
    for name in ("parashari", "kp", "jaimini", "astronomy", "shared_charts", "integration"):
        assert (ROOT / "engine" / name / "__init__.py").is_file()


def test_rule_directories_exist_per_tradition() -> None:
    for tradition in ("parashari", "kp", "jaimini"):
        assert (ROOT / "knowledge" / "rules" / tradition).is_dir()
