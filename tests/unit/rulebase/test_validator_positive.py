"""Valid rulebases must pass with zero errors: every rule type, status, namespace and link kind."""

import pytest
from rulebase_builders import (
    append_version,
    calculation_content,
    citation,
    convention_content,
    interpretive_content,
    make_rule,
    source,
    write_repo,
)

from knowledge.rulebase.loader import RulebasePaths


def ok(check, tmp_path, rules, **kwargs):
    paths = write_repo(tmp_path, rules, **kwargs)
    report = check(paths)
    assert report.errors == [], [f.format() for f in report.errors]
    return report


@pytest.mark.parametrize("status", ["DRAFT", "PROVISIONAL", "VERIFIED", "REJECTED"])
@pytest.mark.parametrize(
    "rule_type", ["INTERPRETIVE_RULE", "CALCULATION_RULE", "CALCULATION_CONVENTION"]
)
def test_every_rule_type_is_valid_in_every_single_record_status(check, tmp_path, rule_type, status):
    report = ok(check, tmp_path, [make_rule(rule_type=rule_type, status=status)])
    assert report.rules_checked == 1


@pytest.mark.parametrize(
    ("rule_id", "namespace_dir"),
    [
        ("PAR-ASP-0001", "parashari"),
        ("KP-SUB-0001", "kp"),
        ("JAI-KRK-0001", "jaimini"),
        ("SHR-NAK-0001", "shared"),
    ],
)
def test_four_separate_namespaces(check, tmp_path, rule_id, namespace_dir):
    ok(check, tmp_path, [make_rule(rule_id, status="VERIFIED")])
    assert (tmp_path / "knowledge" / "rules" / namespace_dir / f"{rule_id}.yaml").is_file()


def test_same_number_in_different_namespaces_is_not_a_duplicate(check, tmp_path):
    ok(
        check,
        tmp_path,
        [make_rule("PAR-ASP-0001"), make_rule("KP-SUB-0001"), make_rule("JAI-KRK-0001")],
    )


def test_conflicting_traditions_are_separate_records_with_reciprocal_links(check, tmp_path):
    note = "Synthetic: the two traditions give different outcomes"
    a = make_rule(
        "PAR-ASP-0001",
        status="VERIFIED",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "KP-SUB-0001", "note": note}]
        ),
    )
    b = make_rule(
        "KP-SUB-0001",
        status="VERIFIED",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "PAR-ASP-0001", "note": note}]
        ),
    )
    report = ok(check, tmp_path, [a, b])
    assert report.rules_checked == 2


def test_contradicting_source_is_kept_as_alternative_reading(check, tmp_path):
    note = "Synthetic: another edition reads this differently"
    a = make_rule(
        "PAR-ASP-0001",
        content=interpretive_content(
            citations=[citation(), citation("SRC-TEST-A:ch2:v5", "CONTRADICTS")],
            relations=[{"kind": "ALTERNATIVE_READING", "target": "PAR-ASP-0002", "note": note}],
        ),
    )
    b = make_rule(
        "PAR-ASP-0002",
        content=interpretive_content(
            citations=[citation("SRC-TEST-A:ch2:v5")],
            relations=[{"kind": "ALTERNATIVE_READING", "target": "PAR-ASP-0001", "note": note}],
        ),
    )
    ok(check, tmp_path, [a, b])


def test_conflicting_sources_status_with_relation(check, tmp_path):
    note = "Synthetic: sources disagree about the outcome"
    a = make_rule(
        "PAR-ASP-0001",
        status="CONFLICTING_SOURCES",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "PAR-ASP-0002", "note": note}]
        ),
    )
    b = make_rule(
        "PAR-ASP-0002",
        status="CONFLICTING_SOURCES",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "PAR-ASP-0001", "note": note}]
        ),
    )
    ok(check, tmp_path, [a, b])


def test_calculation_rule_uses_a_convention_and_interpretive_rule_requires_a_calculation(
    check, tmp_path
):
    convention = make_rule("PAR-AYN-0001", rule_type="CALCULATION_CONVENTION", status="VERIFIED")
    calc = make_rule(
        "PAR-DSH-0001",
        rule_type="CALCULATION_RULE",
        status="VERIFIED",
        content=calculation_content(uses_conventions=["PAR-AYN-0001"]),
    )
    interp = make_rule(
        "PAR-ASP-0001",
        status="VERIFIED",
        content=interpretive_content(requires_calculation_rules=["PAR-DSH-0001"]),
    )
    ok(check, tmp_path, [convention, calc, interp])


def test_tradition_rules_may_depend_on_shared_rules(check, tmp_path):
    shared = make_rule("SHR-NAK-0001", status="VERIFIED")
    par = make_rule(
        "PAR-ASP-0001",
        status="VERIFIED",
        content=interpretive_content(relations=[{"kind": "DEPENDS_ON", "target": "SHR-NAK-0001"}]),
    )
    ok(check, tmp_path, [shared, par])


def test_supersedes_requires_rejected_target_in_same_namespace(check, tmp_path):
    old = make_rule("PAR-ASP-0001", status="REJECTED")
    new = make_rule(
        "PAR-ASP-0002",
        content=interpretive_content(
            relations=[
                {
                    "kind": "SUPERSEDES",
                    "target": "PAR-ASP-0001",
                    "note": "Synthetic: replaced after rejection",
                }
            ]
        ),
    )
    ok(check, tmp_path, [old, new])


def test_new_version_starts_again_and_old_approval_stays_with_old_version(check, tmp_path):
    raw = make_rule(status="VERIFIED")
    append_version(raw, "PROVISIONAL")
    ok(check, tmp_path, [raw])


def test_verified_then_second_version_verified_by_a_second_owner_review(check, tmp_path):
    raw = make_rule(status="VERIFIED")
    append_version(raw, "VERIFIED")
    ok(check, tmp_path, [raw])


def test_convention_verified_when_decision_is_accepted(check, tmp_path):
    ok(
        check,
        tmp_path,
        [make_rule("PAR-AYN-0001", rule_type="CALCULATION_CONVENTION", status="VERIFIED")],
    )


def test_convention_stays_provisional_under_a_proposed_decision(check, tmp_path):
    raw = make_rule(
        "PAR-AYN-0001",
        rule_type="CALCULATION_CONVENTION",
        status="PROVISIONAL",
        content=convention_content(decision_ref="D-902"),
    )
    ok(check, tmp_path, [raw])


def test_independent_validation_recorded_when_an_independent_review_exists(check, tmp_path):
    raw = make_rule(status="VERIFIED")
    entry = raw["versions"][0]
    raw["reviews"].append(
        {
            "review_id": "R-0002",
            "rule_version": 1,
            "content_hash": entry["content_hash"],
            "actor": "INDEPENDENT_REVIEWER",
            "review_type": "INDEPENDENT_REVIEW",
            "verdict": "APPROVE",
            "date": entry["created"],
            "reviewer_name": "Synthetic Reviewer",
            "stated_qualifications": "Synthetic qualifications as stated",
        }
    )
    raw["independent_validation"] = "RECORDED"
    ok(check, tmp_path, [raw])


def test_independent_calculation_review_with_named_implementation(check, tmp_path):
    raw = make_rule(rule_type="CALCULATION_RULE", status="PROVISIONAL")
    entry = raw["versions"][0]
    raw["reviews"].append(
        {
            "review_id": "R-0001",
            "rule_version": 1,
            "content_hash": entry["content_hash"],
            "actor": "INDEPENDENT_REVIEWER",
            "review_type": "INDEPENDENT_CALCULATION",
            "verdict": "APPROVE",
            "date": entry["created"],
            "evidence": {
                "independent_source": {
                    "name": "SyntheticCalc",
                    "version": "1.0",
                    "settings": {"mode": "x"},
                }
            },
        }
    )
    raw["independent_validation"] = "RECORDED"
    ok(check, tmp_path, [raw])


def test_claude_code_and_model_reviews_are_allowed_but_never_independent(check, tmp_path):
    raw = make_rule(status="PROVISIONAL")
    entry = raw["versions"][0]
    raw["reviews"] += [
        {
            "review_id": "R-0001",
            "rule_version": 1,
            "content_hash": entry["content_hash"],
            "actor": "CLAUDE_CODE",
            "review_type": "DRAFT_REVIEW",
            "verdict": "APPROVE",
            "date": entry["created"],
        },
        {
            "review_id": "R-0002",
            "rule_version": 1,
            "content_hash": entry["content_hash"],
            "actor": "MODEL",
            "provider": "synthetic-provider",
            "model_id": "synthetic-model-id",
            "review_type": "TECHNICAL_VALIDATION",
            "verdict": "APPROVE",
            "date": entry["created"],
            "evidence": {"tests": ["test_synthetic"]},
        },
    ]
    ok(check, tmp_path, [raw])


def test_chara_dasha_method_rule_with_complete_edition(check, tmp_path):
    raw = make_rule(
        "JAI-CHD-0001",
        rule_type="CALCULATION_RULE",
        status="PROVISIONAL",
        content=calculation_content(method_id="CHARA_KNRAO_SYNTHETIC1"),
    )
    ok(check, tmp_path, [raw])


def test_empty_rulebase_is_valid(check, tmp_path):
    report = ok(check, tmp_path, [])
    assert report.rules_checked == 0


def test_draft_may_cite_a_source_not_yet_catalogued_but_gets_a_warning(check, tmp_path):
    raw = make_rule(
        status="DRAFT",
        content=interpretive_content(citations=[citation("SRC-UNLISTED:ch1:v1")]),
    )
    report = ok(check, tmp_path, [raw])
    assert "CITATION-SOURCE" in report.codes()


def test_incomplete_draft_is_allowed(check, tmp_path):
    raw = make_rule(status="DRAFT", content={"title": "Only a title so far"})
    ok(check, tmp_path, [raw])


def test_source_catalogue_accepts_unconfirmed_source_without_file(check, tmp_path):
    ok(
        check,
        tmp_path,
        [make_rule(status="DRAFT")],
        sources=[source("SRC-TEST-A", ownership="UNCONFIRMED", rights="UNKNOWN")],
    )


def test_paths_object_points_at_repo_layout(tmp_path):
    paths = RulebasePaths.from_root(tmp_path)
    assert paths.rules_dir == tmp_path / "knowledge" / "rules"
    assert paths.decisions_file == tmp_path / "docs" / "decisions.md"
