"""Append-only history against a git baseline (`--against REF`)."""

import copy
import subprocess
from pathlib import Path

import pytest
from rulebase_builders import (
    append_version,
    interpretive_content,
    make_rule,
    rule_path,
    seal,
    write_repo,
    write_rule,
)

from knowledge.rulebase.history import HistoryError, check_append_only
from knowledge.rulebase.loader import RulebasePaths, load_rulebase

GIT = [
    "git",
    "-c",
    "user.name=Test",
    "-c",
    "user.email=test@example.invalid",
    "-c",
    "commit.gpgsign=false",
]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        [*GIT, "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


def committed_repo(tmp_path: Path, rules: list[dict]) -> tuple[RulebasePaths, str]:
    paths = write_repo(tmp_path, rules)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "baseline")
    return paths, "HEAD"


def history_codes(paths: RulebasePaths, ref: str = "HEAD") -> set[str]:
    return {f.code for f in check_append_only(load_rulebase(paths), ref)}


def test_appending_versions_reviews_and_events_is_allowed(tmp_path):
    raw = make_rule(status="VERIFIED")
    paths, ref = committed_repo(tmp_path, [raw])
    append_version(raw, "VERIFIED")
    write_rule(paths, raw)
    assert history_codes(paths, ref) == set()


def test_adding_a_new_rule_file_is_allowed(tmp_path):
    paths, ref = committed_repo(tmp_path, [make_rule()])
    write_rule(paths, make_rule("KP-SUB-0001"))
    assert history_codes(paths, ref) == set()


def test_changing_only_tooling_fields_is_allowed(tmp_path):
    raw = make_rule()
    paths, ref = committed_repo(tmp_path, [raw])
    raw["terms"] = ["another_term"]
    raw["tests"] = ["test_something"]
    write_rule(paths, raw)
    assert history_codes(paths, ref) == set()


def test_editing_a_recorded_version_even_with_a_fresh_hash_is_caught(tmp_path):
    raw = make_rule(status="VERIFIED")
    paths, ref = committed_repo(tmp_path, [raw])
    altered = copy.deepcopy(raw)
    altered["versions"][0]["content"]["statement"] = "Quietly rewritten after approval."
    seal(altered)  # the hash now matches, so only the history check can see the tampering
    write_rule(paths, altered)
    assert "HIST-ENTRY-ALTERED" in history_codes(paths, ref)


def test_removing_a_recorded_review_is_caught(tmp_path):
    raw = make_rule(status="VERIFIED")
    paths, ref = committed_repo(tmp_path, [raw])
    raw["reviews"] = []
    write_rule(paths, raw)
    assert "HIST-ENTRY-REMOVED" in history_codes(paths, ref)


def test_changing_a_lifecycle_event_is_caught(tmp_path):
    raw = make_rule(status="REJECTED")
    paths, ref = committed_repo(tmp_path, [raw])
    raw["lifecycle"][-1]["reason"] = "Reworded reason"
    write_rule(paths, raw)
    assert "HIST-ENTRY-ALTERED" in history_codes(paths, ref)


def test_deleting_a_rule_file_is_caught(tmp_path):
    raw = make_rule()
    paths, ref = committed_repo(tmp_path, [raw])
    rule_path(paths, raw).unlink()
    assert "HIST-DELETED" in history_codes(paths, ref)


def test_changing_rule_identity_is_caught(tmp_path):
    raw = make_rule()
    paths, ref = committed_repo(tmp_path, [raw])
    raw["topic"] = "yoga"
    write_rule(paths, raw)
    assert "HIST-IDENTITY-CHANGED" in history_codes(paths, ref)


def test_unknown_ref_is_a_tool_error(tmp_path):
    paths, _ = committed_repo(tmp_path, [make_rule()])
    with pytest.raises(HistoryError):
        history_codes(paths, "no-such-ref")


def test_not_a_git_repository_is_a_tool_error(tmp_path):
    paths = write_repo(tmp_path, [make_rule()])
    with pytest.raises(HistoryError):
        history_codes(paths, "HEAD")


def test_history_compares_against_any_earlier_ref(tmp_path):
    raw = make_rule(status="PROVISIONAL")
    paths, _ = committed_repo(tmp_path, [raw])
    append_version(raw, "PROVISIONAL")
    write_rule(paths, raw)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "second")
    assert history_codes(paths, "HEAD~1") == set()
    raw["versions"][0]["content"] = interpretive_content(
        statement="Rewritten history of version one."
    )
    seal(raw)
    write_rule(paths, raw)
    assert "HIST-ENTRY-ALTERED" in history_codes(paths, "HEAD~1")


def test_unreadable_baseline_file_is_a_warning_not_a_crash(tmp_path):
    paths = write_repo(tmp_path, [])
    broken = paths.rules_dir / "parashari" / "PAR-ASP-0001.yaml"
    broken.write_text(
        "rule_id: a\nrule_id: b\n", encoding="utf-8"
    )  # duplicate key: not valid strict YAML
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "baseline with a broken file")
    write_rule(paths, make_rule())
    findings = check_append_only(load_rulebase(paths), "HEAD")
    assert [f.code for f in findings] == ["HIST-BASELINE-UNREADABLE"]
    assert findings[0].severity.value == "WARNING"
