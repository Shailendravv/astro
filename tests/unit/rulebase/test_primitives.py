"""YAML strictness, content hashing, decision-log parsing, lifecycle helpers, source catalogue loading."""

from datetime import date

import pytest
from rulebase_builders import append_version, make_rule, source, write_repo

from knowledge.rulebase.decisions import load_decisions, parse_decisions
from knowledge.rulebase.hashing import canonical_json, version_hash
from knowledge.rulebase.lifecycle import (
    current_status,
    ever_complete,
    latest_version,
    served_version,
    states_by_version,
)
from knowledge.rulebase.models import RuleFile
from knowledge.rulebase.sources import load_catalog, source_id_of
from knowledge.rulebase.yamlio import YamlError, dump_yaml, load_yaml_text

# ---------------------------------------------------------------- YAML


def test_duplicate_keys_are_rejected_not_silently_overridden():
    with pytest.raises(YamlError, match="duplicate key"):
        load_yaml_text("a: 1\na: 2\n")


def test_duplicate_keys_nested_are_rejected():
    with pytest.raises(YamlError, match="duplicate key"):
        load_yaml_text("outer:\n  inner: 1\n  inner: 2\n")


def test_unsafe_yaml_tags_are_refused():
    with pytest.raises(YamlError):
        load_yaml_text("x: !!python/object/apply:os.system ['echo hi']\n")


def test_dates_and_null_round_trip():
    text = dump_yaml({"d": date(2026, 11, 18), "n": None, "s": "हिन्दी"})
    assert load_yaml_text(text) == {"d": date(2026, 11, 18), "n": None, "s": "हिन्दी"}
    assert "हिन्दी" in text  # Devanagari stays readable in files


# ---------------------------------------------------------------- hashing


def test_hash_is_independent_of_key_order_but_sensitive_to_content():
    a = version_hash("PAR-ASP-0001", 1, {"x": 1, "y": [1, 2]})
    assert a == version_hash("PAR-ASP-0001", 1, {"y": [1, 2], "x": 1})
    assert a != version_hash("PAR-ASP-0001", 1, {"x": 1, "y": [2, 1]})
    assert a != version_hash("PAR-ASP-0001", 1, {"x": 2, "y": [1, 2]})


def test_hash_binds_rule_id_and_version_number():
    content = {"x": 1}
    assert version_hash("PAR-ASP-0001", 1, content) != version_hash("PAR-ASP-0002", 1, content)
    assert version_hash("PAR-ASP-0001", 1, content) != version_hash("PAR-ASP-0001", 2, content)
    assert version_hash("PAR-ASP-0001", 1, content).startswith("sha256:")


def test_canonical_json_keeps_devanagari_and_handles_dates():
    assert canonical_json({"b": "हि", "a": date(2026, 1, 2)}) == '{"a":"2026-01-02","b":"हि"}'
    with pytest.raises(TypeError):
        canonical_json({"x": object()})


# ---------------------------------------------------------------- decision log


DECISIONS = """\
## D-001 Local first — ACCEPTED (2026-11-17)
## D-003 Ayanamsha — PROPOSED (rev. 2)
## D-011 Books — OPEN (recommended list PROPOSED, rev. 2)
## D-012 Groq — OPEN → ID RECORDED (2026-11-18)
## D-027 Payloads — ACCEPTED (principle, 2026-11-17) / PROPOSED (values)
## D-030 No Anthropic — ACCEPTED (owner, 2026-11-18)
Not a heading D-099 — ACCEPTED
"""


@pytest.mark.parametrize(
    ("decision_id", "accepted"),
    [
        ("D-001", True),
        ("D-003", False),
        ("D-011", False),
        ("D-012", False),
        ("D-027", False),  # mixed ACCEPTED / PROPOSED is not fully accepted
        ("D-030", True),
    ],
)
def test_decision_acceptance_is_read_from_the_heading(decision_id, accepted):
    assert parse_decisions(DECISIONS)[decision_id].accepted is accepted


def test_non_headings_are_ignored_and_missing_file_is_none(tmp_path):
    assert "D-099" not in parse_decisions(DECISIONS)
    assert load_decisions(tmp_path / "absent.md") is None


def test_the_real_decision_log_marks_the_proposed_conventions_as_not_accepted():
    """Owner decision 2026-11-18: D-003 to D-010 and D-025 stay PROPOSED."""
    from pathlib import Path

    decisions = load_decisions(Path(__file__).parents[3] / "docs" / "decisions.md")
    assert decisions is not None
    for decision_id in [
        "D-003",
        "D-004",
        "D-005",
        "D-006",
        "D-007",
        "D-008",
        "D-009",
        "D-010",
        "D-025",
    ]:
        assert decisions[decision_id].accepted is False, decision_id
    assert decisions["D-022"].accepted is True
    assert decisions["D-030"].accepted is True


# ---------------------------------------------------------------- lifecycle helpers


def test_status_belongs_to_the_version_and_a_new_version_starts_again():
    raw = make_rule(status="VERIFIED")
    append_version(raw, "DRAFT")
    model = RuleFile.model_validate(raw)
    assert {v: str(s) for v, s in states_by_version(model).items()} == {1: "VERIFIED", 2: "DRAFT"}
    assert latest_version(model) == 2
    assert current_status(model) == "DRAFT"
    assert served_version(model) == 1


def test_ever_complete_distinguishes_drafts():
    draft = RuleFile.model_validate(make_rule(status="DRAFT"))
    verified = RuleFile.model_validate(make_rule(status="VERIFIED"))
    rejected = RuleFile.model_validate(make_rule(status="REJECTED"))
    assert not ever_complete(draft, 1)
    assert ever_complete(verified, 1)
    assert ever_complete(rejected, 1)  # it was PROVISIONAL (complete) before the owner rejected it


def test_served_version_is_none_without_a_verified_version():
    assert served_version(RuleFile.model_validate(make_rule(status="PROVISIONAL"))) is None


# ---------------------------------------------------------------- source catalogue


def test_catalogue_loads_sources_and_ignores_templates(tmp_path):
    paths = write_repo(
        tmp_path,
        [],
        sources=[
            source("SRC-TEST-A"),
            source("SRC-TEST-B", ownership="UNCONFIRMED", rights="UNKNOWN"),
        ],
    )
    (paths.catalog_dir / "_template.yaml.example").write_text("not: a source\n", encoding="utf-8")
    (paths.catalog_dir / "README.md").write_text("notes\n", encoding="utf-8")
    sources, findings, seen = load_catalog(paths.catalog_dir)
    assert sorted(sources) == ["SRC-TEST-A", "SRC-TEST-B"]
    assert findings == []
    assert seen == 2


def test_missing_catalogue_directory_is_an_empty_catalogue(tmp_path):
    assert load_catalog(tmp_path / "nowhere") == ({}, [], 0)


def test_citation_id_to_source_id():
    assert source_id_of("SRC-X-V1:ch24:v12") == "SRC-X-V1"


def test_the_real_catalogue_is_empty_because_no_book_is_confirmed():
    """Q-014: nothing is catalogued until the owner supplies the inventory."""
    from pathlib import Path

    catalogue = Path(__file__).parents[3] / "knowledge" / "source_catalog"
    assert [p.name for p in catalogue.glob("*.yaml")] == []
