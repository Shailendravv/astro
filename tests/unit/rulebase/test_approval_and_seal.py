"""Owner approval (version-bound, interactive only, rolled back if invalid) and sealing."""

from datetime import date

import pytest
from rulebase_builders import (
    TODAY,
    append_version,
    citation,
    convention_content,
    interpretive_content,
    make_rule,
    rule_path,
    write_repo,
)

from knowledge.rulebase.approval import ApprovalError, apply_owner_decision, seal_file
from knowledge.rulebase.lifecycle import current_status, served_version
from knowledge.rulebase.loader import load_rulebase
from knowledge.rulebase.models import RuleFile
from knowledge.rulebase.retrieval import load_runtime_rules
from knowledge.rulebase.validator import validate_rulebase
from knowledge.rulebase.yamlio import dump_yaml, load_yaml_text

RULE_ID = "PAR-ASP-0001"


def decide(paths, decision="APPROVE", *, version=1, typed=RULE_ID, interactive=True, **kwargs):
    return apply_owner_decision(
        paths,
        RULE_ID,
        version,
        decision,
        interactive=interactive,
        typed_confirmation=typed,
        today=kwargs.pop("today", TODAY),
        **kwargs,
    )


def status_of(paths, rule_id=RULE_ID):
    return current_status(load_rulebase(paths).rules[rule_id].model)


def test_approval_records_a_version_bound_owner_review_and_verifies(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    decide(paths, notes="Checked against the quoted passage")
    rulebase = load_rulebase(paths)
    model = rulebase.rules[RULE_ID].model
    assert current_status(model) == "VERIFIED"
    review = model.reviews[-1]
    assert review.actor.value == "OWNER"
    assert review.review_type.value == "SOURCE_APPROVAL"
    assert review.recorded_via.value == "CLI_INTERACTIVE"
    assert review.content_hash == model.versions[0].content_hash
    assert review.evidence.citation_ids == ["SRC-TEST-A:ch1:v1"]
    assert review.date == TODAY
    event = model.lifecycle[-1]
    assert (event.from_status, event.to_status, event.review_id) == (
        "PROVISIONAL",
        "VERIFIED",
        review.review_id,
    )
    assert validate_rulebase(paths, today=TODAY).errors == []


def test_approval_refused_without_an_interactive_terminal_and_nothing_changes(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    before = rule_path(paths, make_rule()).read_bytes()
    with pytest.raises(ApprovalError, match="interactive terminal"):
        decide(paths, interactive=False)
    assert rule_path(paths, make_rule()).read_bytes() == before


@pytest.mark.parametrize("typed", ["", "par-asp-0001", "PAR-ASP-0002", " PAR-ASP-0001"])
def test_approval_refused_unless_the_exact_rule_id_is_typed(tmp_path, typed):
    paths = write_repo(tmp_path, [make_rule(status="PROVISIONAL")])
    with pytest.raises(ApprovalError, match="confirmation"):
        decide(paths, typed=typed)
    assert status_of(paths) == "PROVISIONAL"


def test_draft_cannot_be_approved(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="DRAFT")])
    with pytest.raises(ApprovalError):
        decide(paths)


def test_already_verified_cannot_be_approved_again(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="VERIFIED")])
    with pytest.raises(ApprovalError):
        decide(paths)


def test_only_the_latest_version_can_be_decided(tmp_path):
    raw = make_rule(status="PROVISIONAL")
    append_version(raw, "PROVISIONAL")
    paths = write_repo(tmp_path, [raw])
    with pytest.raises(ApprovalError, match="latest version"):
        decide(paths, version=1)


def test_approving_a_new_version_leaves_the_old_approval_in_place(tmp_path):
    raw = make_rule(status="VERIFIED")
    append_version(raw, "PROVISIONAL")
    paths = write_repo(tmp_path, [raw])
    decide(paths, version=2, today=date(2026, 11, 18))
    model = load_rulebase(paths).rules[RULE_ID].model
    assert [r.rule_version for r in model.reviews] == [1, 2]
    assert model.reviews[0].content_hash != model.reviews[1].content_hash
    assert served_version(model) == 2


def test_rule_with_validation_errors_cannot_be_decided(tmp_path):
    raw = make_rule(
        status="PROVISIONAL",
        content=interpretive_content(citations=[citation(relation="COMMENTARY")]),
    )
    paths = write_repo(tmp_path, [raw])
    with pytest.raises(ApprovalError, match="validation errors"):
        decide(paths)


def test_approval_that_would_leave_the_rule_invalid_is_rolled_back_byte_for_byte(tmp_path):
    raw = make_rule(
        status="PROVISIONAL", content=interpretive_content(citations=[citation(reviewed=False)])
    )
    paths = write_repo(tmp_path, [raw])
    path = rule_path(paths, raw)
    before = path.read_bytes()
    with pytest.raises(ApprovalError, match="VERIFIED-PASSAGE-UNREVIEWED"):
        decide(paths)
    assert path.read_bytes() == before


def test_convention_cannot_be_verified_while_its_decision_is_only_proposed(tmp_path):
    raw = make_rule(
        "PAR-AYN-0001",
        rule_type="CALCULATION_CONVENTION",
        content=convention_content(decision_ref="D-902"),
    )
    paths = write_repo(tmp_path, [raw])
    path = rule_path(paths, raw)
    before = path.read_bytes()
    with pytest.raises(ApprovalError, match="VERIFIED-DECISION-NOT-ACCEPTED"):
        apply_owner_decision(
            paths,
            "PAR-AYN-0001",
            1,
            "APPROVE",
            interactive=True,
            typed_confirmation="PAR-AYN-0001",
            today=TODAY,
        )
    assert path.read_bytes() == before


def test_rejection_needs_a_reason_and_removes_the_rule_from_retrieval(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="VERIFIED")])
    assert len(load_runtime_rules(paths, today=TODAY).rules) == 1
    with pytest.raises(ApprovalError, match="reason"):
        decide(paths, "REJECT")
    decide(paths, "REJECT", reason="Passage was misread")
    assert status_of(paths) == "REJECTED"
    assert load_runtime_rules(paths, today=TODAY).rules == ()


def test_rejecting_twice_is_refused(tmp_path):
    paths = write_repo(tmp_path, [make_rule(status="REJECTED")])
    with pytest.raises(ApprovalError, match="already"):
        decide(paths, "REJECT", reason="again")


def test_unknown_rule_is_refused(tmp_path):
    paths = write_repo(tmp_path, [])
    with pytest.raises(ApprovalError, match="not found"):
        decide(paths)


# ---------------------------------------------------------------- sealing


def test_seal_writes_missing_hashes_and_the_rule_then_validates(tmp_path):
    raw = make_rule(status="PROVISIONAL")
    for entry in raw["versions"]:
        del entry["content_hash"]
    for review in raw["reviews"]:
        review.pop("content_hash", None)
    paths = write_repo(tmp_path, [raw])
    path = rule_path(paths, raw)
    assert "SCHEMA" in validate_rulebase(paths, today=TODAY).error_codes()  # unsealed is not valid
    assert seal_file(path) == [1]
    assert validate_rulebase(paths, today=TODAY).errors == []
    assert seal_file(path) == []  # second run changes nothing


def test_seal_never_overwrites_a_wrong_hash(tmp_path):
    raw = make_rule(status="PROVISIONAL")
    raw["versions"][0]["content"]["statement"] = "Edited after sealing, hash left as it was."
    paths = write_repo(tmp_path, [raw])
    path = rule_path(paths, raw)
    before = path.read_bytes()
    assert seal_file(path) == []
    assert path.read_bytes() == before
    assert "VERSION-HASH" in validate_rulebase(paths, today=TODAY).error_codes()


def test_seal_rejects_files_that_are_not_rules(tmp_path):
    path = tmp_path / "x.yaml"
    path.write_text("just: text\n", encoding="utf-8")
    with pytest.raises(ApprovalError):
        seal_file(path)


def test_rule_files_round_trip_through_the_writer_without_changing_meaning(tmp_path):
    raw = make_rule(status="VERIFIED")
    paths = write_repo(tmp_path, [raw])
    path = rule_path(paths, raw)
    reloaded = load_yaml_text(path.read_text(encoding="utf-8"))
    path.write_text(dump_yaml(reloaded), encoding="utf-8")
    assert validate_rulebase(paths, today=TODAY).errors == []
    assert RuleFile.model_validate(reloaded).rule_id == RULE_ID
