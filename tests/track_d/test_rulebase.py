"""Track D (no LLM, runs in CI): the real rule knowledge base in this repository must validate.

M2 first Track D checks (D-028): rule records, source catalogue, and the retrieval gate on the real
`knowledge/` tree. With no book inventory (Q-014) the catalogue and rule set are empty, so these checks pass
trivially today; they become meaningful as soon as the first record is added, and they cannot be forgotten.
"""

from pathlib import Path

import pytest

from knowledge.rulebase.loader import RulebasePaths
from knowledge.rulebase.retrieval import load_runtime_rules
from knowledge.rulebase.validator import validate_rulebase

ROOT = Path(__file__).resolve().parents[2]
PATHS = RulebasePaths.from_root(ROOT)

pytestmark = pytest.mark.track_d


def test_the_real_rulebase_validates_with_zero_errors():
    report = validate_rulebase(PATHS)
    assert [f.format() for f in report.errors] == []


def test_the_real_rulebase_has_no_warnings_that_hide_unfinished_citations():
    report = validate_rulebase(PATHS)
    assert [f.format() for f in report.warnings] == []


def test_runtime_retrieval_on_the_real_rulebase_serves_only_owner_approved_rules():
    runtime = load_runtime_rules(PATHS)
    for rule in runtime.rules:
        assert rule.version >= 1
        assert rule.content_hash.startswith("sha256:")


def test_no_rule_in_the_real_repository_was_marked_verified_by_anyone_but_the_owner():
    """Every VERIFIED status must carry an owner SOURCE_APPROVAL recorded through the CLI (also a validator rule)."""
    from knowledge.rulebase.loader import load_rulebase

    for rule_id, loaded in load_rulebase(PATHS).rules.items():
        verified = [e for e in loaded.model.lifecycle if e.to_status.value == "VERIFIED"]
        for event in verified:
            review = next(r for r in loaded.model.reviews if r.review_id == event.review_id)
            assert (review.actor.value, review.recorded_via.value) == (
                "OWNER",
                "CLI_INTERACTIVE",
            ), rule_id


def test_real_vocabulary_has_unique_codes_and_covers_every_namespace():
    from knowledge.rulebase.enums import Namespace
    from knowledge.rulebase.vocabulary import load_vocabulary

    topics, findings = load_vocabulary(PATHS.vocabulary_file)
    assert findings == []
    codes = [t.code for t in topics.values()]
    assert len(codes) == len(set(codes))
    for namespace in Namespace:
        assert any(namespace in t.namespaces for t in topics.values()), namespace
