"""Append-only history check against a git ref (`jyotish rules validate --against <ref>`).

The hash check proves a version was not edited *within* a file; this check proves nothing already recorded at
the baseline ref was changed or removed. Versions, reviews, and lifecycle events may only be appended, and a
rule's identity fields never change. Rule files are never deleted: a rule is rejected, not removed.
"""

import subprocess
from pathlib import Path
from typing import Any

from knowledge.rulebase.findings import Finding, error, warning
from knowledge.rulebase.loader import Rulebase
from knowledge.rulebase.yamlio import YamlError, load_yaml_text

APPEND_ONLY_LISTS = ("versions", "reviews", "lifecycle")
IMMUTABLE_FIELDS = ("rule_id", "namespace", "rule_type", "topic")


class HistoryError(RuntimeError):
    """The baseline could not be read (bad ref, not a git repository)."""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise HistoryError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def check_append_only(rulebase: Rulebase, ref: str) -> list[Finding]:
    repo = rulebase.paths.root
    rules_dir = rulebase.paths.rules_dir.relative_to(repo).as_posix()
    try:
        _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    except HistoryError as problem:
        raise HistoryError(f"cannot resolve baseline ref {ref!r}: {problem}") from problem
    listing = _git(repo, "ls-tree", "-r", "--name-only", ref, "--", rules_dir)
    findings: list[Finding] = []
    for path in (line for line in listing.splitlines() if line.endswith(".yaml")):
        rel = path[len(rules_dir) + 1 :]
        if rel.split("/")[-1].startswith("_"):
            continue
        try:
            before = load_yaml_text(_git(repo, "show", f"{ref}:{path}"))
        except YamlError as problem:
            findings.append(
                warning(
                    "HIST-BASELINE-UNREADABLE",
                    f"baseline file is not valid YAML, skipped: {problem}",
                    file=rel,
                )
            )
            continue
        if not isinstance(before, dict):
            continue
        current = next((lr for lr in rulebase.rules.values() if lr.rel == rel), None)
        rule_id = str(before.get("rule_id", "?"))
        if current is None:
            findings.append(
                error(
                    "HIST-DELETED",
                    "rule file existed at the baseline but is missing or unreadable now. Rules are rejected by the owner, never deleted",
                    rule_id=rule_id,
                    file=rel,
                )
            )
            continue
        findings.extend(_compare(rule_id, rel, before, current.raw))
    return findings


def _compare(rule_id: str, rel: str, before: dict[str, Any], now: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for name in IMMUTABLE_FIELDS:
        if before.get(name) != now.get(name):
            findings.append(
                error(
                    "HIST-IDENTITY-CHANGED",
                    f"'{name}' changed from {before.get(name)!r} to {now.get(name)!r}",
                    rule_id=rule_id,
                    file=rel,
                )
            )
    for name in APPEND_ONLY_LISTS:
        old = before.get(name) or []
        new = now.get(name) or []
        if len(new) < len(old):
            findings.append(
                error(
                    "HIST-ENTRY-REMOVED",
                    f"{name}: {len(old) - len(new)} recorded entr{'y' if len(old) - len(new) == 1 else 'ies'} removed",
                    rule_id=rule_id,
                    file=rel,
                )
            )
            continue
        for index, old_entry in enumerate(old):
            if new[index] != old_entry:
                findings.append(
                    error(
                        "HIST-ENTRY-ALTERED",
                        f"{name}[{index}] was recorded at the baseline and has been changed. Recorded versions, reviews and events are append-only",
                        rule_id=rule_id,
                        file=rel,
                    )
                )
    return findings
