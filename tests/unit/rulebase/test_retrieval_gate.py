"""Runtime retrieval gate: unapproved research drafts never reach the interpretation layer."""

import dataclasses
from datetime import date

import pytest
from rulebase_builders import (
    TODAY,
    add_event,
    add_owner_review,
    append_version,
    calculation_content,
    interpretive_content,
    make_rule,
    write_repo,
)

from knowledge.rulebase.enums import Namespace, RuleType
from knowledge.rulebase.loader import load_rulebase
from knowledge.rulebase.retrieval import (
    RulebaseInvalidError,
    RuntimeRule,
    _owner_approved,
    build_runtime_rules,
    load_runtime_rules,
)


def get_rule(runtime, rule_id) -> RuntimeRule:
    rule = runtime.get(rule_id)
    assert rule is not None, f"{rule_id} was not served"
    return rule


def served_ids(paths) -> list[str]:
    return [r.rule_id for r in load_runtime_rules(paths, today=TODAY).rules]


@pytest.mark.parametrize("status", ["DRAFT", "PROVISIONAL", "REJECTED"])
def test_unapproved_or_rejected_rules_are_never_served(tmp_path, status):
    paths = write_repo(tmp_path, [make_rule(status=status)])
    assert served_ids(paths) == []


def test_conflicting_sources_records_are_not_served_until_the_owner_approves_each(tmp_path):
    note = "Synthetic: sources disagree"
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
    assert served_ids(write_repo(tmp_path, [a, b])) == []


def test_only_verified_rules_are_served_among_a_mix(tmp_path):
    rules = [
        make_rule("PAR-ASP-0001", status="VERIFIED"),
        make_rule("PAR-ASP-0002", status="PROVISIONAL"),
        make_rule("PAR-ASP-0003", status="DRAFT"),
        make_rule("PAR-ASP-0004", status="REJECTED"),
    ]
    assert served_ids(write_repo(tmp_path, rules)) == ["PAR-ASP-0001"]


def test_verified_rule_rejected_later_is_withdrawn(tmp_path):
    raw = make_rule(status="VERIFIED")
    review_id = add_owner_review(raw, 1, "REJECT", 15)
    add_event(
        raw,
        1,
        "VERIFIED",
        "REJECTED",
        15,
        owner=True,
        review_id=review_id,
        reason="Found to be wrong",
    )
    assert served_ids(write_repo(tmp_path, [raw])) == []


def test_a_forged_verified_status_without_owner_approval_makes_retrieval_refuse(tmp_path):
    raw = make_rule(status="VERIFIED")
    event = raw["lifecycle"][-1]
    event["actor"] = "CLAUDE_CODE"
    del event["recorded_via"]
    del event["review_id"]
    raw["reviews"] = []
    paths = write_repo(tmp_path, [raw])
    with pytest.raises(RulebaseInvalidError) as problem:
        load_runtime_rules(paths, today=TODAY)
    assert "EVENT-OWNER-ONLY" in {e.code for e in problem.value.errors}


def test_an_owner_review_typed_into_the_file_is_not_an_approval(tmp_path):
    raw = make_rule(status="VERIFIED")
    raw["reviews"][0]["recorded_via"] = "FILE_EDIT"
    with pytest.raises(RulebaseInvalidError):
        load_runtime_rules(write_repo(tmp_path, [raw]), today=TODAY)


def test_edited_content_invalidates_the_approval_and_retrieval_refuses(tmp_path):
    raw = make_rule(status="VERIFIED")
    raw["versions"][0]["content"]["effect"] = "Changed after the owner approved the original text"
    with pytest.raises(RulebaseInvalidError) as problem:
        load_runtime_rules(write_repo(tmp_path, [raw]), today=TODAY)
    assert "VERSION-HASH" in {e.code for e in problem.value.errors}


def test_one_invalid_rule_anywhere_stops_all_retrieval(tmp_path):
    good = make_rule("PAR-ASP-0001", status="VERIFIED")
    broken = make_rule("KP-SUB-0001")
    broken["topic"] = "no_such_topic"
    with pytest.raises(RulebaseInvalidError):
        load_runtime_rules(write_repo(tmp_path, [good, broken]), today=TODAY)


def test_defence_in_depth_the_retriever_rechecks_approval_itself(tmp_path):
    """Even if the validator were bypassed, an unapproved version is not served."""
    paths = write_repo(tmp_path, [make_rule(status="VERIFIED")])
    loaded = load_rulebase(paths).rules["PAR-ASP-0001"]
    assert _owner_approved(loaded, 1) is True
    stripped = dataclasses.replace(loaded, model=loaded.model.model_copy(update={"reviews": []}))
    assert _owner_approved(stripped, 1) is False
    other_hash = loaded.model.reviews[0].model_copy(update={"content_hash": "sha256:" + "2" * 64})
    tampered = dataclasses.replace(
        loaded, model=loaded.model.model_copy(update={"reviews": [other_hash]})
    )
    assert _owner_approved(tampered, 1) is False
    via_file = loaded.model.reviews[0].model_copy(update={"recorded_via": "FILE_EDIT"})
    forged = dataclasses.replace(
        loaded, model=loaded.model.model_copy(update={"reviews": [via_file]})
    )
    assert _owner_approved(forged, 1) is False


def test_approved_old_version_stays_served_while_a_newer_draft_is_in_progress(tmp_path):
    raw = make_rule(status="VERIFIED")
    append_version(raw, "DRAFT", statement="Newer draft wording that is not approved.")
    paths = write_repo(tmp_path, [raw])
    (served,) = load_runtime_rules(paths, today=TODAY).rules
    assert served.version == 1
    assert "Newer draft" not in served.statement


def test_a_rejected_newer_version_leaves_the_approved_one_in_place(tmp_path):
    raw = make_rule(status="VERIFIED")
    append_version(raw, "REJECTED")
    (served,) = load_runtime_rules(write_repo(tmp_path, [raw]), today=TODAY).rules
    assert served.version == 1


def test_newest_approved_version_wins(tmp_path):
    raw = make_rule(status="VERIFIED")
    append_version(raw, "VERIFIED")
    (served,) = load_runtime_rules(write_repo(tmp_path, [raw]), today=TODAY).rules
    assert served.version == 2


def test_served_rules_carry_text_and_citation_ids_but_no_review_material(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="VERIFIED")])
    (rule,) = load_runtime_rules(paths, today=TODAY).rules
    assert rule.citation_ids == ("SRC-TEST-A:ch1:v1",)
    names = {f.name for f in dataclasses.fields(RuntimeRule)}
    assert names.isdisjoint(
        {"quote", "quotes", "reviews", "lifecycle", "ambiguity_notes", "notes", "citations"}
    )
    assert "Synthetic quote" not in repr(rule)


def test_interpretive_view_excludes_calculation_rules_and_conventions(tmp_path):
    rules = [
        make_rule("PAR-ASP-0001", status="VERIFIED"),
        make_rule("PAR-AYN-0001", rule_type="CALCULATION_CONVENTION", status="VERIFIED"),
        make_rule("PAR-DSH-0001", rule_type="CALCULATION_RULE", status="VERIFIED"),
    ]
    runtime = load_runtime_rules(write_repo(tmp_path, rules), today=TODAY)
    assert [r.rule_id for r in runtime.interpretive().rules] == ["PAR-ASP-0001"]
    assert {r.rule_type for r in runtime.rules} == set(RuleType)
    convention = runtime.get("PAR-AYN-0001")
    assert convention is not None
    assert "ayanamsha=synthetic-value (D-901)" in convention.convention


def test_conflicting_traditions_are_served_as_separate_linked_rules(tmp_path):
    note = "Synthetic: the traditions differ"
    par = make_rule(
        "PAR-ASP-0001",
        status="VERIFIED",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "KP-SUB-0001", "note": note}]
        ),
    )
    kp = make_rule(
        "KP-SUB-0001",
        status="VERIFIED",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "PAR-ASP-0001", "note": note}]
        ),
    )
    runtime = load_runtime_rules(write_repo(tmp_path, [par, kp]), today=TODAY)
    assert [r.rule_id for r in runtime.rules] == [
        "KP-SUB-0001",
        "PAR-ASP-0001",
    ]  # two records, never merged
    assert [link.rule_id for link in get_rule(runtime, "PAR-ASP-0001").conflicts] == ["KP-SUB-0001"]


def test_conflict_link_to_an_unapproved_rule_is_not_exposed(tmp_path):
    note = "Synthetic: sources differ"
    a = make_rule(
        "PAR-ASP-0001",
        status="VERIFIED",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "PAR-ASP-0002", "note": note}]
        ),
    )
    b = make_rule(
        "PAR-ASP-0002",
        status="PROVISIONAL",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "PAR-ASP-0001", "note": note}]
        ),
    )
    runtime = load_runtime_rules(write_repo(tmp_path, [a, b]), today=TODAY)
    assert get_rule(runtime, "PAR-ASP-0001").conflicts == ()
    assert runtime.get("PAR-ASP-0002") is None


def test_single_tradition_view_has_only_that_tradition_plus_shared_and_no_foreign_ids(tmp_path):
    note = "Synthetic: the traditions differ"
    par = make_rule(
        "PAR-ASP-0001",
        status="VERIFIED",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "KP-SUB-0001", "note": note}]
        ),
    )
    kp = make_rule(
        "KP-SUB-0001",
        status="VERIFIED",
        content=interpretive_content(
            relations=[{"kind": "CONFLICTS_WITH", "target": "PAR-ASP-0001", "note": note}]
        ),
    )
    shared = make_rule("SHR-NAK-0001", status="VERIFIED")
    jai = make_rule("JAI-KRK-0001", status="VERIFIED")
    runtime = load_runtime_rules(write_repo(tmp_path, [par, kp, shared, jai]), today=TODAY)
    view = runtime.for_single_tradition(Namespace.PARASHARI)
    assert sorted(r.rule_id for r in view.rules) == ["PAR-ASP-0001", "SHR-NAK-0001"]
    assert (
        get_rule(view, "PAR-ASP-0001").conflicts == ()
    )  # KP-SUB-0001 is not named in a Parashari prompt
    assert "KP-SUB-0001" not in repr(view)
    with pytest.raises(ValueError, match="choose a tradition"):
        runtime.for_single_tradition(Namespace.SHARED)


def test_empty_rulebase_serves_nothing(tmp_path):
    assert served_ids(write_repo(tmp_path, [])) == []


def test_build_from_loaded_rulebase_matches_load_from_paths(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="VERIFIED")])
    assert build_runtime_rules(load_rulebase(paths), today=TODAY) == load_runtime_rules(
        paths, today=TODAY
    )


def test_future_dated_records_are_invalid_so_nothing_is_served(tmp_path):
    raw = make_rule(status="VERIFIED")
    raw["lifecycle"][-1]["date"] = date(2030, 1, 1)
    with pytest.raises(RulebaseInvalidError):
        load_runtime_rules(write_repo(tmp_path, [raw]), today=TODAY)


def test_calculation_rule_runtime_view_has_formal_spec(tmp_path):
    raw = make_rule(
        "PAR-DSH-0001",
        rule_type="CALCULATION_RULE",
        status="VERIFIED",
        content=calculation_content(),
    )
    runtime = load_runtime_rules(write_repo(tmp_path, [raw]), today=TODAY)
    assert get_rule(runtime, "PAR-DSH-0001").formal_spec.startswith("synthetic_output")
