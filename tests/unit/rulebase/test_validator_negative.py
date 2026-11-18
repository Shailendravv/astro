"""Negative tests: every validator code is triggered by a minimal broken rulebase.

Each case builds a synthetic repository that is valid except for one defect, and asserts that the matching
code is reported (as an ERROR, or as a WARNING where marked).
"""

import copy
import shutil
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest
from rulebase_builders import (
    CREATED,
    add_event,
    append_version,
    calculation_content,
    citation,
    convention_content,
    interpretive_content,
    make_rule,
    rule_path,
    seal,
    source,
    write_repo,
)

from knowledge.rulebase.loader import RulebasePaths
from knowledge.rulebase.yamlio import dump_yaml

Builder = Callable[[Path], RulebasePaths]
CASES: list = []


def case(code: str, *, warning: bool = False):
    def register(fn: Builder) -> Builder:
        CASES.append(pytest.param(code, fn, warning, id=f"{code}:{fn.__name__}"))
        return fn

    return register


def one(tmp: Path, raw: dict, **kwargs) -> RulebasePaths:
    return write_repo(tmp, [raw], **kwargs)


def sealed(raw: dict) -> dict:
    return seal(raw)


def link(
    kind: str, target: str, note: str | None = "Synthetic note explaining the difference"
) -> dict:
    relation = {"kind": kind, "target": target}
    if note is not None:
        relation["note"] = note
    return relation


# ====================================================================== file and identity


@case("FILE-YAML")
def duplicate_yaml_key(tmp):
    paths = write_repo(tmp, [])
    (paths.rules_dir / "parashari" / "PAR-ASP-0001.yaml").write_text(
        "rule_id: PAR-ASP-0001\nrule_id: PAR-ASP-0002\n", encoding="utf-8"
    )
    return paths


@case("FILE-YAML")
def yaml_not_a_mapping(tmp):
    paths = write_repo(tmp, [])
    (paths.rules_dir / "parashari" / "PAR-ASP-0001.yaml").write_text(
        "- just\n- a list\n", encoding="utf-8"
    )
    return paths


@case("SCHEMA")
def unknown_top_level_key(tmp):
    raw = make_rule()
    raw["surprise"] = 1
    return one(tmp, raw)


@case("SCHEMA")
def missing_required_field(tmp):
    raw = make_rule()
    del raw["lifecycle"]
    return one(tmp, raw)


@case("SCHEMA")
def invalid_enum_value(tmp):
    raw = make_rule()
    raw["rule_type"] = "VIBES"
    return one(tmp, raw)


@case("FILE-SCHEMA-VERSION")
def wrong_schema_version(tmp):
    return one(tmp, make_rule(schema_version=2))


@case("RULE-ID-FORMAT")
def bad_rule_id_format(tmp):
    raw = make_rule()
    raw["rule_id"] = "PAR-ASP-1"
    return one(tmp, sealed(raw))


@case("RULE-ID-NAMESPACE")
def prefix_belongs_to_another_namespace(tmp):
    raw = make_rule("PAR-ASP-0001")
    raw["namespace"] = "KP"
    return one(tmp, raw)


@case("RULE-DIR-NAMESPACE")
def file_in_wrong_directory(tmp):
    raw = make_rule()
    paths = one(tmp, raw)
    shutil.move(rule_path(paths, raw), paths.rules_dir / "kp" / "PAR-ASP-0001.yaml")
    return paths


@case("RULE-FILENAME")
def file_name_differs_from_rule_id(tmp):
    raw = make_rule()
    paths = one(tmp, raw)
    shutil.move(rule_path(paths, raw), paths.rules_dir / "parashari" / "other-name.yaml")
    return paths


@case("RULE-DUPLICATE")
def same_rule_id_in_two_files(tmp):
    raw = make_rule()
    paths = one(tmp, raw)
    shutil.copy(rule_path(paths, raw), paths.rules_dir / "parashari" / "PAR-ASP-0001-b.yaml")
    return paths


@case("TOPIC-UNKNOWN")
def topic_not_in_vocabulary(tmp):
    return one(tmp, make_rule(topic="astrology_vibes"))


@case("TOPIC-CODE")
def topic_code_differs_from_rule_id(tmp):
    return one(tmp, make_rule("PAR-ASP-0001", topic="yoga"))


@case("TOPIC-NAMESPACE")
def topic_not_allowed_in_namespace(tmp):
    return one(tmp, make_rule("PAR-SUB-0001"))  # sub_lord is a KP topic


@case("TERM-FORMAT")
def glossary_key_not_snake_case(tmp):
    return one(tmp, make_rule(terms=["Bad Term"]))


@case("LOAD-UNKNOWN-NAMESPACE")
def unknown_namespace_directory(tmp):
    paths = write_repo(tmp, [])
    (paths.rules_dir / "tantric").mkdir()
    (paths.rules_dir / "tantric" / "X-ASP-0001.yaml").write_text("a: 1\n", encoding="utf-8")
    return paths


@case("LOAD-EXTENSION")
def yml_extension(tmp):
    paths = write_repo(tmp, [])
    (paths.rules_dir / "parashari" / "PAR-ASP-0001.yml").write_text("a: 1\n", encoding="utf-8")
    return paths


@case("LOAD-MISPLACED")
def rule_file_outside_namespace_directory(tmp):
    paths = write_repo(tmp, [])
    (paths.rules_dir / "PAR-ASP-0001.yaml").write_text("a: 1\n", encoding="utf-8")
    return paths


@case("LOAD-STRAY-DIR")
def nested_directory_in_namespace(tmp):
    paths = write_repo(tmp, [])
    (paths.rules_dir / "parashari" / "nested").mkdir()
    return paths


@case("LOAD-NO-RULES-DIR")
def no_rules_directory(tmp):
    return RulebasePaths.from_root(tmp)


# ====================================================================== rule types are kept apart


@case("CONTENT-SCHEMA")
def interpretive_rule_with_calculation_field(tmp):
    return one(tmp, make_rule(content=interpretive_content(formal_spec="x = y")))


@case("CONTENT-SCHEMA")
def calculation_rule_with_interpretive_field(tmp):
    return one(
        tmp, make_rule(rule_type="CALCULATION_RULE", content=calculation_content(effect="x"))
    )


@case("CONTENT-SCHEMA")
def convention_with_conditions(tmp):
    return one(
        tmp,
        make_rule(
            "PAR-AYN-0001",
            rule_type="CALCULATION_CONVENTION",
            content=convention_content(conditions=[]),
        ),
    )


@case("CONTENT-SCHEMA")
def unknown_convention_setting(tmp):
    content = convention_content()
    content["convention"]["setting_key"] = "vibes"
    return one(tmp, make_rule("PAR-AYN-0001", rule_type="CALCULATION_CONVENTION", content=content))


# ====================================================================== versions and hashes


@case("VERSION-SEQUENCE")
def version_numbers_skip(tmp):
    raw = make_rule()
    append_version(raw)
    raw["versions"][1]["version"] = 3
    return one(tmp, sealed(raw))


@case("VERSION-HASH")
def recorded_content_edited_after_sealing(tmp):
    raw = make_rule(status="VERIFIED")
    raw["versions"][0]["content"]["statement"] = "Edited after approval, hash not updated."
    return one(tmp, raw)


@case("VERSION-HASH-FORMAT")
def malformed_hash(tmp):
    raw = make_rule()
    raw["versions"][0]["content_hash"] = "abc"
    return one(tmp, raw)


@case("VERSION-CHANGE-NOTE")
def blank_change_note(tmp):
    raw = make_rule()
    raw["versions"][0]["change_note"] = "  "
    return one(tmp, raw)


@case("VERSION-ACTOR")
def model_author_without_model_id(tmp):
    raw = make_rule()
    raw["versions"][0]["created_by"] = {"actor": "MODEL"}
    return one(tmp, raw)


@case("VERSION-ACTOR")
def independent_reviewer_as_author(tmp):
    raw = make_rule()
    raw["versions"][0]["created_by"] = {"actor": "INDEPENDENT_REVIEWER"}
    return one(tmp, raw)


@case("VERSION-DATE-FUTURE")
def version_created_in_the_future(tmp):
    raw = make_rule()
    raw["versions"][0]["created"] = date(2030, 1, 1)
    return one(tmp, raw)


@case("VERSION-DATE-ORDER")
def second_version_older_than_first(tmp):
    raw = make_rule()
    append_version(raw)
    raw["versions"][1]["created"] = date(2026, 11, 1)
    return one(tmp, raw)


@case("VERSION-NOOP", warning=True)
def second_version_identical_content(tmp):
    raw = make_rule()
    append_version(raw, statement=raw["versions"][0]["content"]["statement"])
    return one(tmp, raw)


# ====================================================================== lifecycle


@case("EVENT-ID")
def wrong_event_id(tmp):
    raw = make_rule()
    raw["lifecycle"][0]["event_id"] = "E-0009"
    return one(tmp, raw)


@case("EVENT-VERSION")
def event_for_missing_version(tmp):
    raw = make_rule()
    add_event(raw, 9, None, "DRAFT", 12)
    return one(tmp, raw)


@case("EVENT-MISSING")
def new_version_without_events(tmp):
    raw = make_rule()
    append_version(raw)
    raw["lifecycle"] = raw["lifecycle"][:1]
    return one(tmp, raw)


@case("EVENT-TRANSITION")
def draft_straight_to_conflicting(tmp):
    raw = make_rule(status="DRAFT")
    add_event(raw, 1, "DRAFT", "CONFLICTING_SOURCES", 12, reason="Synthetic")
    return one(tmp, raw)


@case("EVENT-TRANSITION")
def leaving_rejected(tmp):
    raw = make_rule(status="REJECTED")
    add_event(raw, 1, "REJECTED", "PROVISIONAL", 13)
    return one(tmp, raw)


@case("EVENT-TRANSITION")
def verified_back_to_provisional(tmp):
    raw = make_rule(status="VERIFIED")
    add_event(raw, 1, "VERIFIED", "PROVISIONAL", 13)
    return one(tmp, raw)


@case("EVENT-FROM")
def from_does_not_match_history(tmp):
    raw = make_rule()
    raw["lifecycle"][0]["from"] = "DRAFT"
    return one(tmp, raw)


@case("EVENT-OWNER-ONLY")
def claude_code_marks_verified(tmp):
    raw = make_rule(status="VERIFIED")
    event = raw["lifecycle"][-1]
    event["actor"] = "CLAUDE_CODE"
    del event["recorded_via"]
    return one(tmp, raw)


@case("EVENT-OWNER-ONLY")
def owner_event_recorded_by_file_edit(tmp):
    raw = make_rule(status="VERIFIED")
    raw["lifecycle"][-1]["recorded_via"] = "FILE_EDIT"
    return one(tmp, raw)


@case("EVENT-APPROVAL")
def verified_without_review_reference(tmp):
    raw = make_rule(status="VERIFIED")
    del raw["lifecycle"][-1]["review_id"]
    return one(tmp, raw)


@case("EVENT-APPROVAL")
def approval_review_has_wrong_verdict(tmp):
    raw = make_rule(status="VERIFIED")
    raw["reviews"][0]["verdict"] = "REQUEST_CHANGES"
    return one(tmp, raw)


@case("EVENT-APPROVAL")
def approval_bound_to_different_content(tmp):
    raw = make_rule(status="VERIFIED")
    raw["reviews"][0]["content_hash"] = "sha256:" + "0" * 64
    return one(tmp, raw)


@case("EVENT-APPROVAL")
def approval_is_for_an_older_version(tmp):
    raw = make_rule(status="PROVISIONAL")
    append_version(raw, "PROVISIONAL")
    review_id = "R-0001"
    raw["reviews"].append(
        {
            "review_id": review_id,
            "rule_version": 1,
            "content_hash": raw["versions"][0]["content_hash"],
            "actor": "OWNER",
            "review_type": "SOURCE_APPROVAL",
            "verdict": "APPROVE",
            "date": date(2026, 11, 14),
            "recorded_via": "CLI_INTERACTIVE",
            "evidence": {"citation_ids": ["SRC-TEST-A:ch1:v1"]},
        }
    )
    add_event(raw, 2, "PROVISIONAL", "VERIFIED", 14, owner=True, review_id=review_id)
    return one(tmp, raw)


@case("EVENT-APPROVAL")
def approval_review_by_wrong_actor(tmp):
    raw = make_rule(status="VERIFIED")
    raw["reviews"][0]["actor"] = "CLAUDE_CODE"
    return one(tmp, raw)


@case("EVENT-REASON")
def rejection_without_reason(tmp):
    raw = make_rule(status="REJECTED")
    del raw["lifecycle"][-1]["reason"]
    return one(tmp, raw)


@case("EVENT-REASON")
def conflicting_sources_without_reason(tmp):
    raw = make_rule(
        status="CONFLICTING_SOURCES",
        content=interpretive_content(relations=[link("CONFLICTS_WITH", "PAR-ASP-0002")]),
    )
    del raw["lifecycle"][-1]["reason"]
    return one(tmp, raw)


@case("EVENT-CONFLICT-RELATION")
def conflicting_sources_without_a_linked_record(tmp):
    return one(tmp, make_rule(status="CONFLICTING_SOURCES"))


@case("EVENT-DATE-ORDER")
def events_out_of_order(tmp):
    raw = make_rule(status="VERIFIED")
    raw["lifecycle"][-1]["date"] = date(2026, 11, 10)
    return one(tmp, raw)


@case("EVENT-DATE-FUTURE")
def event_in_the_future(tmp):
    raw = make_rule()
    raw["lifecycle"][0]["date"] = date(2030, 1, 1)
    return one(tmp, raw)


@case("EVENT-ACTOR")
def independent_reviewer_records_a_transition(tmp):
    raw = make_rule()
    raw["lifecycle"][0]["actor"] = "INDEPENDENT_REVIEWER"
    return one(tmp, raw)


# ====================================================================== reviews


def with_review(status: str = "PROVISIONAL", **review) -> dict:
    raw = make_rule(status=status)
    entry = raw["versions"][0]
    base = {
        "review_id": f"R-{len(raw['reviews']) + 1:04d}",
        "rule_version": 1,
        "content_hash": entry["content_hash"],
        "actor": "CLAUDE_CODE",
        "review_type": "DRAFT_REVIEW",
        "verdict": "APPROVE",
        "date": CREATED,
    }
    base.update(review)
    raw["reviews"].append(base)
    return raw


@case("REVIEW-ID")
def duplicate_review_id(tmp):
    raw = with_review(review_id="R-0001")
    raw["reviews"].append(copy.deepcopy(raw["reviews"][0]))
    return one(tmp, raw)


@case("REVIEW-ID")
def malformed_review_id(tmp):
    return one(tmp, with_review(review_id="review-one"))


@case("REVIEW-VERSION")
def review_of_missing_version(tmp):
    return one(tmp, with_review(rule_version=7))


@case("REVIEW-HASH")
def review_of_different_content(tmp):
    return one(tmp, with_review(content_hash="sha256:" + "1" * 64))


@case("REVIEW-DATE")
def review_in_the_future(tmp):
    return one(tmp, with_review(date=date(2030, 1, 1)))


@case("REVIEW-DATE")
def review_before_the_version_existed(tmp):
    return one(tmp, with_review(date=date(2026, 11, 1)))


@case("REVIEW-ACTOR-TYPE")
def claude_code_gives_source_approval(tmp):
    return one(
        tmp,
        with_review(
            review_type="SOURCE_APPROVAL", evidence={"citation_ids": ["SRC-TEST-A:ch1:v1"]}
        ),
    )


@case("REVIEW-ACTOR-TYPE")
def owner_gives_a_technical_validation(tmp):
    return one(
        tmp,
        with_review(
            actor="OWNER",
            review_type="TECHNICAL_VALIDATION",
            recorded_via="CLI_INTERACTIVE",
            evidence={"tests": ["t"]},
        ),
    )


@case("REVIEW-OWNER-VIA")
def owner_review_written_by_file_edit(tmp):
    return one(
        tmp,
        with_review(
            actor="OWNER",
            review_type="SOURCE_APPROVAL",
            recorded_via="FILE_EDIT",
            evidence={"citation_ids": ["SRC-TEST-A:ch1:v1"]},
        ),
    )


@case("REVIEW-MODEL")
def model_review_without_exact_model_id(tmp):
    return one(tmp, with_review(actor="MODEL", provider="synthetic-provider"))


@case("REVIEW-INDEPENDENT")
def independent_review_without_qualifications(tmp):
    return one(
        tmp,
        with_review(
            actor="INDEPENDENT_REVIEWER",
            review_type="INDEPENDENT_REVIEW",
            reviewer_name="Synthetic Reviewer",
        ),
    )


@case("REVIEW-INDEPENDENT")
def independent_calculation_without_implementation(tmp):
    return one(
        tmp, with_review(actor="INDEPENDENT_REVIEWER", review_type="INDEPENDENT_CALCULATION")
    )


@case("REVIEW-INDEPENDENT-NAME")
def drafting_tool_recorded_as_independent_reviewer(tmp):
    return one(
        tmp,
        with_review(
            actor="INDEPENDENT_REVIEWER",
            review_type="INDEPENDENT_REVIEW",
            reviewer_name="Claude Code",
            stated_qualifications="none",
        ),
    )


@case("REVIEW-EVIDENCE")
def technical_validation_without_tests(tmp):
    return one(tmp, with_review(review_type="TECHNICAL_VALIDATION"))


@case("REVIEW-EVIDENCE")
def source_approval_lists_no_citations(tmp):
    raw = make_rule(status="VERIFIED")
    raw["reviews"][0]["evidence"] = {"citation_ids": []}
    return one(tmp, raw)


@case("REVIEW-EVIDENCE")
def source_approval_lists_citation_not_in_version(tmp):
    raw = make_rule(status="VERIFIED")
    raw["reviews"][0]["evidence"] = {"citation_ids": ["SRC-TEST-A:ch9:v9"]}
    return one(tmp, raw)


@case("IND-MISMATCH")
def independent_validation_claimed_without_a_review(tmp):
    return one(tmp, make_rule(independent_validation="RECORDED"))


@case("IND-MISMATCH")
def approving_independent_review_but_field_says_none(tmp):
    raw = with_review(
        actor="INDEPENDENT_REVIEWER",
        review_type="INDEPENDENT_REVIEW",
        reviewer_name="Synthetic Reviewer",
        stated_qualifications="Synthetic qualifications",
    )
    return one(tmp, raw)


@case("IND-MISMATCH")
def independent_review_of_an_older_version_does_not_count(tmp):
    raw = with_review(
        actor="INDEPENDENT_REVIEWER",
        review_type="INDEPENDENT_REVIEW",
        reviewer_name="Synthetic Reviewer",
        stated_qualifications="Synthetic qualifications",
    )
    raw["independent_validation"] = "RECORDED"
    append_version(raw)
    return one(tmp, raw)


# ====================================================================== citations and completeness


@case("CITATION-FORMAT")
def malformed_citation_id(tmp):
    return one(
        tmp, make_rule(content=interpretive_content(citations=[citation("not a citation id")]))
    )


@case("CITATION-DUPLICATE")
def same_citation_twice(tmp):
    return one(tmp, make_rule(content=interpretive_content(citations=[citation(), citation()])))


@case("CITATION-QUOTE-LONG")
def quote_longer_than_cap(tmp):
    return one(tmp, make_rule(content=interpretive_content(citations=[citation(quote="x" * 501)])))


@case("CITATION-SOURCE")
def provisional_rule_cites_uncatalogued_source(tmp):
    return one(
        tmp, make_rule(content=interpretive_content(citations=[citation("SRC-NOPE:ch1:v1")]))
    )


@case("CITATION-NO-SUPPORT")
def provisional_rule_without_supporting_citation(tmp):
    return one(
        tmp, make_rule(content=interpretive_content(citations=[citation(relation="COMMENTARY")]))
    )


@case("CITATION-QUOTE-MISSING")
def supporting_citation_without_quote(tmp):
    return one(tmp, make_rule(content=interpretive_content(citations=[citation(quote="")])))


@case("CITATION-LOCATOR")
def supporting_citation_without_page_or_chapter(tmp):
    return one(
        tmp, make_rule(content=interpretive_content(citations=[citation(page=None, chapter=None)]))
    )


@case("CONTENT-INCOMPLETE")
def provisional_with_empty_statement(tmp):
    return one(tmp, make_rule(content=interpretive_content(statement="")))


@case("CONTENT-INCOMPLETE")
def provisional_with_empty_title(tmp):
    return one(tmp, make_rule(content=interpretive_content(title="")))


@case("CONTENT-INCOMPLETE")
def interpretive_rule_without_conditions(tmp):
    return one(tmp, make_rule(content=interpretive_content(conditions=[])))


@case("CONTENT-INCOMPLETE")
def interpretive_rule_without_effect(tmp):
    return one(tmp, make_rule(content=interpretive_content(effect="")))


@case("CONTENT-INCOMPLETE")
def calculation_rule_without_formal_spec(tmp):
    return one(
        tmp, make_rule(rule_type="CALCULATION_RULE", content=calculation_content(formal_spec=""))
    )


@case("CONTENT-INCOMPLETE")
def calculation_rule_without_outputs(tmp):
    return one(
        tmp, make_rule(rule_type="CALCULATION_RULE", content=calculation_content(outputs=[]))
    )


@case("CONTENT-INCOMPLETE")
def convention_without_block(tmp):
    content = convention_content()
    del content["convention"]
    return one(tmp, make_rule("PAR-AYN-0001", rule_type="CALCULATION_CONVENTION", content=content))


@case("CONTENT-INCOMPLETE")
def convention_without_profiles(tmp):
    return one(
        tmp,
        make_rule(
            "PAR-AYN-0001",
            rule_type="CALCULATION_CONVENTION",
            content=convention_content(profiles=()),
        ),
    )


@case("CONTENT-INCOMPLETE")
def convention_without_value_or_alternatives(tmp):
    content = convention_content(chosen_value=None)
    content["convention"]["alternatives"] = []
    return one(tmp, make_rule("PAR-AYN-0001", rule_type="CALCULATION_CONVENTION", content=content))


@case("CONFLICT-NOT-PRESERVED")
def contradicting_source_without_a_separate_record(tmp):
    content = interpretive_content(
        citations=[citation(), citation("SRC-TEST-A:ch2:v5", "CONTRADICTS")]
    )
    return one(tmp, make_rule(content=content))


# ====================================================================== relations and dependencies


@case("REL-TARGET-FORMAT")
def relation_target_not_a_rule_id(tmp):
    return one(tmp, make_rule(content=interpretive_content(relations=[link("DEPENDS_ON", "nope")])))


@case("REL-TARGET-UNKNOWN")
def relation_target_does_not_exist(tmp):
    return one(
        tmp, make_rule(content=interpretive_content(relations=[link("DEPENDS_ON", "PAR-ASP-0099")]))
    )


@case("REL-SELF")
def relation_to_itself(tmp):
    return one(
        tmp, make_rule(content=interpretive_content(relations=[link("DEPENDS_ON", "PAR-ASP-0001")]))
    )


@case("REL-DUPLICATE")
def same_relation_twice(tmp):
    relations = [link("DEPENDS_ON", "PAR-ASP-0002"), link("DEPENDS_ON", "PAR-ASP-0002")]
    return write_repo(
        tmp,
        [make_rule(content=interpretive_content(relations=relations)), make_rule("PAR-ASP-0002")],
    )


@case("REL-CROSS-TRADITION")
def parashari_rule_depends_on_kp_rule(tmp):
    a = make_rule(content=interpretive_content(relations=[link("DEPENDS_ON", "KP-SUB-0001")]))
    return write_repo(tmp, [a, make_rule("KP-SUB-0001")])


@case("REL-CROSS-TRADITION")
def shared_rule_depends_on_tradition_rule(tmp):
    a = make_rule(
        "SHR-NAK-0001", content=interpretive_content(relations=[link("DEPENDS_ON", "PAR-ASP-0001")])
    )
    return write_repo(tmp, [a, make_rule("PAR-ASP-0001")])


@case("REL-CROSS-TRADITION")
def calculation_rule_uses_another_traditions_convention(tmp):
    convention = make_rule(
        "KP-AYN-0001",
        rule_type="CALCULATION_CONVENTION",
        content=convention_content(profiles=("kp-krishnamurti",)),
    )
    calc = make_rule(
        "PAR-DSH-0001",
        rule_type="CALCULATION_RULE",
        content=calculation_content(uses_conventions=["KP-AYN-0001"]),
    )
    return write_repo(tmp, [convention, calc])


@case("REL-SUPERSEDES-NAMESPACE")
def supersedes_across_namespaces(tmp):
    old = make_rule("KP-SUB-0001", status="REJECTED")
    new = make_rule(
        "PAR-ASP-0001", content=interpretive_content(relations=[link("SUPERSEDES", "KP-SUB-0001")])
    )
    return write_repo(tmp, [old, new])


@case("REL-SUPERSEDES-TARGET")
def supersedes_a_rule_the_owner_has_not_rejected(tmp):
    old = make_rule("PAR-ASP-0001", status="PROVISIONAL")
    new = make_rule(
        "PAR-ASP-0002", content=interpretive_content(relations=[link("SUPERSEDES", "PAR-ASP-0001")])
    )
    return write_repo(tmp, [old, new])


@case("REL-NOTE")
def conflict_without_explanation(tmp):
    a = make_rule(
        "PAR-ASP-0001",
        content=interpretive_content(relations=[link("CONFLICTS_WITH", "PAR-ASP-0002", note=None)]),
    )
    b = make_rule(
        "PAR-ASP-0002",
        content=interpretive_content(relations=[link("CONFLICTS_WITH", "PAR-ASP-0001", note=None)]),
    )
    return write_repo(tmp, [a, b])


@case("REL-NOTE")
def supersedes_without_reason(tmp):
    old = make_rule("PAR-ASP-0001", status="REJECTED")
    new = make_rule(
        "PAR-ASP-0002",
        content=interpretive_content(relations=[link("SUPERSEDES", "PAR-ASP-0001", note=None)]),
    )
    return write_repo(tmp, [old, new])


@case("REL-ASYMMETRIC")
def conflict_not_linked_back(tmp):
    a = make_rule(
        "PAR-ASP-0001",
        content=interpretive_content(relations=[link("CONFLICTS_WITH", "KP-SUB-0001")]),
    )
    return write_repo(tmp, [a, make_rule("KP-SUB-0001")])


@case("REL-ASYMMETRIC")
def conflict_linked_back_with_a_different_kind(tmp):
    a = make_rule(
        "PAR-ASP-0001",
        content=interpretive_content(relations=[link("CONFLICTS_WITH", "PAR-ASP-0002")]),
    )
    b = make_rule(
        "PAR-ASP-0002",
        content=interpretive_content(relations=[link("ALTERNATIVE_READING", "PAR-ASP-0001")]),
    )
    return write_repo(tmp, [a, b])


@case("TYPE-LINK-UNKNOWN")
def calculation_rule_uses_missing_convention(tmp):
    return one(
        tmp,
        make_rule(
            "PAR-DSH-0001",
            rule_type="CALCULATION_RULE",
            content=calculation_content(uses_conventions=["PAR-AYN-0099"]),
        ),
    )


@case("TYPE-LINK")
def calculation_rule_uses_an_interpretive_rule_as_convention(tmp):
    calc = make_rule(
        "PAR-DSH-0001",
        rule_type="CALCULATION_RULE",
        content=calculation_content(uses_conventions=["PAR-ASP-0001"]),
    )
    return write_repo(tmp, [calc, make_rule("PAR-ASP-0001")])


@case("TYPE-LINK")
def interpretive_rule_requires_a_convention_instead_of_a_calculation(tmp):
    convention = make_rule("PAR-AYN-0001", rule_type="CALCULATION_CONVENTION")
    interp = make_rule(
        "PAR-ASP-0001", content=interpretive_content(requires_calculation_rules=["PAR-AYN-0001"])
    )
    return write_repo(tmp, [convention, interp])


@case("DEP-CYCLE")
def circular_dependency(tmp):
    a = make_rule(
        "PAR-ASP-0001",
        content=interpretive_content(relations=[link("DEPENDS_ON", "PAR-ASP-0002", None)]),
    )
    b = make_rule(
        "PAR-ASP-0002",
        content=interpretive_content(relations=[link("DEPENDS_ON", "PAR-ASP-0001", None)]),
    )
    return write_repo(tmp, [a, b])


@case("DEP-UNVERIFIED")
def verified_rule_rests_on_an_unapproved_rule(tmp):
    a = make_rule(
        "PAR-ASP-0001",
        status="VERIFIED",
        content=interpretive_content(relations=[link("DEPENDS_ON", "PAR-ASP-0002", None)]),
    )
    return write_repo(tmp, [a, make_rule("PAR-ASP-0002", status="PROVISIONAL")])


# ====================================================================== conventions


def convention(rule_id: str = "PAR-AYN-0001", status: str = "PROVISIONAL", **kwargs) -> dict:
    return make_rule(
        rule_id,
        rule_type="CALCULATION_CONVENTION",
        status=status,
        content=convention_content(**kwargs),
    )


@case("CONV-DECISION-FORMAT")
def decision_ref_malformed(tmp):
    return one(tmp, convention(decision_ref="decision three"))


@case("CONV-DECISIONS-MISSING")
def decision_log_absent(tmp):
    return one(tmp, convention(), decisions=None)


@case("CONV-DECISION-UNKNOWN")
def decision_not_in_log(tmp):
    return one(tmp, convention(decision_ref="D-999"))


@case("CONV-SETTING-SCOPE")
def dasha_year_days_for_a_jaimini_profile(tmp):
    return one(
        tmp,
        convention("JAI-DSH-0001", setting_key="dasha_year_days", profiles=("jaimini-lahiri-7k",)),
    )


@case("CONV-SETTING-SCOPE")
def karaka_scheme_in_parashari_namespace(tmp):
    return one(tmp, convention("PAR-AYN-0001", setting_key="karaka_scheme"))


@case("CONV-PROFILE-UNKNOWN")
def unknown_profile_key(tmp):
    return one(tmp, convention(profiles=("parashari-default",)))


@case("CONV-PROFILE-NAMESPACE")
def parashari_convention_targets_kp_profile(tmp):
    return one(tmp, convention(profiles=("kp-krishnamurti",)))


@case("CONV-COUPLING")
def karaka_scheme_depends_on_dasha_method(tmp):
    karaka = make_rule(
        "JAI-KRK-0001",
        rule_type="CALCULATION_CONVENTION",
        content=convention_content(
            setting_key="karaka_scheme",
            profiles=("jaimini-lahiri-7k",),
            relations=[link("DEPENDS_ON", "JAI-DSH-0001", None)],
        ),
    )
    dasha = make_rule(
        "JAI-DSH-0001",
        rule_type="CALCULATION_CONVENTION",
        content=convention_content(
            setting_key="jaimini_dasha_method", profiles=("jaimini-lahiri-7k",)
        ),
    )
    return write_repo(tmp, [karaka, dasha])


@case("CONV-COUPLING-CALC", warning=True)
def calculation_rule_uses_both_karaka_and_dasha_conventions(tmp):
    karaka = convention(
        "JAI-KRK-0001", setting_key="karaka_scheme", profiles=("jaimini-lahiri-7k",)
    )
    dasha = convention(
        "JAI-DSH-0001", setting_key="jaimini_dasha_method", profiles=("jaimini-lahiri-7k",)
    )
    calc = make_rule(
        "JAI-CHD-0001",
        rule_type="CALCULATION_RULE",
        content=calculation_content(uses_conventions=["JAI-KRK-0001", "JAI-DSH-0001"]),
    )
    return write_repo(tmp, [karaka, dasha, calc])


@case("VERIFIED-DECISION-NOT-ACCEPTED")
def verified_convention_under_proposed_decision(tmp):
    return one(tmp, convention(status="VERIFIED", decision_ref="D-902"))


@case("VERIFIED-DECISION-NOT-ACCEPTED")
def verified_convention_under_mixed_status_decision(tmp):
    return one(tmp, convention(status="VERIFIED", decision_ref="D-903"))


@case("VERIFIED-NO-VALUE")
def verified_convention_without_chosen_value(tmp):
    content = convention_content(chosen_value=None)
    content["convention"]["alternatives"] = [{"value": "a"}, {"value": "b"}]
    return one(
        tmp,
        make_rule(
            "PAR-AYN-0001", rule_type="CALCULATION_CONVENTION", status="VERIFIED", content=content
        ),
    )


# ====================================================================== Chara Dasha method (D-008)


@case("METHOD-ID")
def method_id_malformed(tmp):
    return one(
        tmp,
        make_rule(
            "JAI-CHD-0001",
            rule_type="CALCULATION_RULE",
            content=calculation_content(method_id="CHARA_OTHER_X"),
        ),
    )


@case("METHOD-NAMESPACE")
def chara_dasha_method_in_parashari_namespace(tmp):
    return one(
        tmp,
        make_rule(
            "PAR-DSH-0001",
            rule_type="CALCULATION_RULE",
            content=calculation_content(method_id="CHARA_KNRAO_X1"),
        ),
    )


@case("CHARA-EDITION")
def chara_dasha_rule_cites_source_without_edition(tmp):
    raw = make_rule(
        "JAI-CHD-0001",
        rule_type="CALCULATION_RULE",
        content=calculation_content(method_id="CHARA_KNRAO_X1"),
    )
    return one(tmp, raw, sources=[source(edition=None)])


# ====================================================================== VERIFIED preconditions


@case("VERIFIED-PASSAGE-UNREVIEWED")
def verified_rule_cites_unreviewed_passage(tmp):
    return one(
        tmp,
        make_rule(
            status="VERIFIED", content=interpretive_content(citations=[citation(reviewed=False)])
        ),
    )


@case("VERIFIED-EVIDENCE")
def approval_does_not_cover_the_reviewed_citation(tmp):
    content = interpretive_content(
        citations=[citation(), citation("SRC-TEST-A:ch2:v2", reviewed=False)]
    )
    raw = make_rule(status="VERIFIED", content=content)
    raw["reviews"][0]["evidence"] = {"citation_ids": ["SRC-TEST-A:ch2:v2"]}
    return one(tmp, raw)


@case("VERIFIED-SOURCE-OWNERSHIP")
def verified_rule_cites_unconfirmed_source(tmp):
    return one(
        tmp,
        make_rule(status="VERIFIED"),
        sources=[source(ownership="UNCONFIRMED", rights="UNKNOWN")],
    )


@case("VERIFIED-SOURCE-EDITION")
def verified_rule_cites_source_without_edition(tmp):
    return one(tmp, make_rule(status="VERIFIED"), sources=[source(edition=None)])


# ====================================================================== sources and vocabulary


def source_file(tmp: Path, name: str, data: dict) -> RulebasePaths:
    paths = write_repo(tmp, [], sources=[])
    (paths.catalog_dir / name).write_text(dump_yaml(data), encoding="utf-8")
    return paths


@case("SRC-ID")
def source_id_malformed(tmp):
    return source_file(tmp, "bad-id.yaml", source("bad-id"))


@case("SRC-FILENAME")
def source_file_name_differs(tmp):
    return source_file(tmp, "something-else.yaml", source("SRC-TEST-A"))


@case("SRC-SCHEMA")
def source_with_unknown_field(tmp):
    return source_file(tmp, "SRC-TEST-A.yaml", source("SRC-TEST-A", shiny="yes"))


@case("SRC-SCHEMA-VERSION")
def source_wrong_schema_version(tmp):
    return source_file(tmp, "SRC-TEST-A.yaml", source("SRC-TEST-A", schema_version=3))


@case("SRC-DUPLICATE")
def source_id_defined_twice(tmp):
    paths = source_file(tmp, "SRC-TEST-A.yaml", source("SRC-TEST-A"))
    (paths.catalog_dir / "SRC-TEST-A-copy.yaml").write_text(
        dump_yaml(source("SRC-TEST-A")), encoding="utf-8"
    )
    return paths


@case("SRC-UNCONFIRMED-INGESTED")
def unconfirmed_source_has_a_checksum(tmp):
    return source_file(
        tmp, "SRC-TEST-A.yaml", source("SRC-TEST-A", ownership="UNCONFIRMED", sha256="a" * 64)
    )


@case("SRC-FILE-PATH")
def source_file_path_inside_repo(tmp):
    return source_file(
        tmp, "SRC-TEST-A.yaml", source("SRC-TEST-A", file_path="knowledge/books/x.pdf")
    )


@case("SRC-SHA256")
def source_checksum_malformed(tmp):
    return source_file(tmp, "SRC-TEST-A.yaml", source("SRC-TEST-A", sha256="xyz"))


@case("VOCAB-MISSING")
def vocabulary_file_missing(tmp):
    paths = write_repo(tmp, [])
    paths.vocabulary_file.unlink()
    return paths


@case("VOCAB-SCHEMA")
def vocabulary_not_valid(tmp):
    paths = write_repo(tmp, [])
    paths.vocabulary_file.write_text("schema_version: 1\ntopics: nope\n", encoding="utf-8")
    return paths


@case("VOCAB-CODE")
def vocabulary_reuses_a_code(tmp):
    paths = write_repo(tmp, [])
    paths.vocabulary_file.write_text(
        dump_yaml(
            {
                "schema_version": 1,
                "topics": {
                    "one": {"code": "AAA", "namespaces": ["PARASHARI"]},
                    "two": {"code": "AAA", "namespaces": ["KP"]},
                },
            }
        ),
        encoding="utf-8",
    )
    return paths


@case("VOCAB-NAMESPACES")
def vocabulary_topic_allows_no_namespace(tmp):
    paths = write_repo(tmp, [])
    paths.vocabulary_file.write_text(
        dump_yaml({"schema_version": 1, "topics": {"one": {"code": "AAA", "namespaces": []}}}),
        encoding="utf-8",
    )
    return paths


# ====================================================================== the test


@pytest.mark.parametrize(("code", "builder", "as_warning"), CASES)
def test_defect_is_reported(check, tmp_path, code, builder, as_warning):
    report = check(builder(tmp_path))
    found = {f.code for f in report.findings if (f.severity.value == "WARNING") == as_warning}
    assert code in found, f"expected {code}; got {sorted(report.codes())}"


def test_every_documented_error_code_has_at_least_one_negative_case():
    """Guards the guard: a new validator code must come with a test case."""
    import re

    source_text = (Path(__file__).parents[3] / "knowledge" / "rulebase").glob("*.py")
    used = set()
    for path in source_text:
        used |= set(re.findall(r'"([A-Z]+(?:-[A-Z0-9]+)+)"', path.read_text(encoding="utf-8")))
    covered = {param.values[0] for param in CASES}
    # codes used only by other test groups (history, retrieval) or that are structural constants
    ignored = {"CHARA-KNRAO"} | {c for c in used if c.startswith(("HIST-", "SHA-"))}
    candidates = {
        c
        for c in used
        if c.split("-")[0]
        in {
            "FILE",
            "RULE",
            "TOPIC",
            "TERM",
            "LOAD",
            "CONTENT",
            "VERSION",
            "EVENT",
            "REVIEW",
            "IND",
            "CITATION",
            "CONFLICT",
            "REL",
            "TYPE",
            "DEP",
            "CONV",
            "METHOD",
            "CHARA",
            "VERIFIED",
            "SRC",
            "VOCAB",
            "SCHEMA",
        }
    } - ignored
    missing = sorted(candidates - covered)
    assert not missing, f"validator codes without a negative test: {missing}"


def test_valid_baseline_for_these_builders_has_no_errors(check, tmp_path):
    """The mutations above start from a clean baseline, so the reported code is the defect."""
    assert check(write_repo(tmp_path, [make_rule(status="VERIFIED")])).errors == []
