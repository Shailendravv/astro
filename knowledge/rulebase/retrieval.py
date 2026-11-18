"""Runtime rule retrieval: the only door through which rules reach the interpretation layer.

Gate (owner requirement 6): nothing that is not owner-approved can pass through.
  1. The whole rulebase must validate with zero errors, otherwise retrieval refuses to run at all.
  2. Only a version whose lifecycle status is VERIFIED is served, and it is re-checked here, independently of
     the validator, for an OWNER SOURCE_APPROVAL APPROVE review bound to that version's exact content hash and
     recorded through the interactive CLI.
  3. DRAFT, PROVISIONAL, CONFLICTING_SOURCES and REJECTED versions are never served, whatever they claim.
  4. Output carries no reviews, quotes, ambiguity notes, or lifecycle history: rule text and citation IDs only
     (book text is not sent to providers beyond the capped passages, security.md section 4).

Conflicting records are served as separate rules with explicit links (never merged). A single-tradition view
contains only that tradition's rules plus SHARED, and drops links that would name another tradition's rule.
"""

from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from knowledge.rulebase.enums import (
    Actor,
    CitationRelation,
    Namespace,
    RecordedVia,
    ReviewType,
    RuleType,
    Status,
    Verdict,
)
from knowledge.rulebase.findings import Finding
from knowledge.rulebase.lifecycle import events_for, served_version
from knowledge.rulebase.loader import LoadedRule, Rulebase, RulebasePaths, load_rulebase
from knowledge.rulebase.models import (
    CalculationContent,
    ConventionContent,
    InterpretiveContent,
)
from knowledge.rulebase.validator import CONFLICT_KINDS, validate_loaded


class RulebaseInvalidError(RuntimeError):
    """The rulebase has validation errors, so nothing is served."""

    def __init__(self, errors: list[Finding]) -> None:
        self.errors = errors
        shown = "; ".join(f"{e.code} {e.rule_id or ''}".strip() for e in errors[:5])
        super().__init__(f"rulebase is invalid ({len(errors)} errors: {shown}); retrieval refused")


@dataclass(frozen=True)
class RuleLink:
    kind: str  # CONFLICTS_WITH | ALTERNATIVE_READING
    rule_id: str


@dataclass(frozen=True)
class RuntimeRule:
    rule_id: str
    namespace: Namespace
    rule_type: RuleType
    topic: str
    version: int
    content_hash: str
    title: str
    statement: str
    conditions: tuple[str, ...] = ()
    effect: str = ""
    exceptions: tuple[str, ...] = ()
    formal_spec: str = ""
    convention: str = ""
    citation_ids: tuple[str, ...] = ()
    conflicts: tuple[RuleLink, ...] = ()


@dataclass(frozen=True)
class RuntimeRuleSet:
    rules: tuple[RuntimeRule, ...]

    def get(self, rule_id: str) -> RuntimeRule | None:
        return next((r for r in self.rules if r.rule_id == rule_id), None)

    def of_type(self, *types: RuleType) -> "RuntimeRuleSet":
        return RuntimeRuleSet(tuple(r for r in self.rules if r.rule_type in types))

    def interpretive(self) -> "RuntimeRuleSet":
        """What the interpretation layer asks for. Calculation rules and conventions are engine-side."""
        return self.of_type(RuleType.INTERPRETIVE_RULE)

    def for_namespaces(self, *namespaces: Namespace) -> "RuntimeRuleSet":
        keep = set(namespaces)
        kept = [r for r in self.rules if r.namespace in keep]
        ids = {r.rule_id for r in kept}
        # Drop links to rules outside the view so another tradition's IDs never leak into a prompt.
        cleaned = tuple(
            replace(r, conflicts=tuple(link for link in r.conflicts if link.rule_id in ids))
            for r in kept
        )
        return RuntimeRuleSet(cleaned)

    def for_single_tradition(self, tradition: Namespace) -> "RuntimeRuleSet":
        if tradition is Namespace.SHARED:
            raise ValueError("choose a tradition: PARASHARI, KP or JAIMINI")
        return self.for_namespaces(tradition, Namespace.SHARED)


def _owner_approved(lr: LoadedRule, version: int) -> bool:
    """Independent re-check that this exact version carries a valid owner approval."""
    entry = next((e for e in lr.model.versions if e.version == version), None)
    if entry is None:
        return False
    for event in events_for(lr.model, version):
        if event.to_status is not Status.VERIFIED:
            continue
        review = next((r for r in lr.model.reviews if r.review_id == event.review_id), None)
        if (
            review is not None
            and review.actor is Actor.OWNER
            and review.review_type is ReviewType.SOURCE_APPROVAL
            and review.verdict is Verdict.APPROVE
            and review.recorded_via is RecordedVia.CLI_INTERACTIVE
            and review.rule_version == version
            and review.content_hash == entry.content_hash
            and event.actor is Actor.OWNER
            and event.recorded_via is RecordedVia.CLI_INTERACTIVE
        ):
            return True
    return False


def _to_runtime(lr: LoadedRule, version: int, retrievable_ids: set[str]) -> RuntimeRule:
    content = lr.contents[version]
    entry = next(e for e in lr.model.versions if e.version == version)
    conflicts = tuple(
        RuleLink(r.kind.value, r.target)
        for r in content.relations
        if r.kind in CONFLICT_KINDS and r.target in retrievable_ids
    )
    citation_ids = tuple(
        c.citation_id for c in content.citations if c.relation is CitationRelation.SUPPORTS
    )
    fields: dict[str, Any] = {
        "rule_id": lr.rule_id,
        "namespace": lr.model.namespace,
        "rule_type": lr.model.rule_type,
        "topic": lr.model.topic,
        "version": version,
        "content_hash": entry.content_hash,
        "title": content.title,
        "statement": content.statement,
        "citation_ids": citation_ids,
        "conflicts": conflicts,
    }
    if isinstance(content, InterpretiveContent):
        fields["conditions"] = tuple(c.text for c in content.conditions)
        fields["effect"] = content.effect
        fields["exceptions"] = tuple(e.text for e in content.exceptions)
    elif isinstance(content, CalculationContent):
        fields["formal_spec"] = content.formal_spec
    elif isinstance(content, ConventionContent) and content.convention is not None:
        convention = content.convention
        fields["convention"] = (
            f"{convention.setting_key.value}={convention.chosen_value} ({convention.decision_ref})"
        )
    return RuntimeRule(**fields)


def build_runtime_rules(rulebase: Rulebase, *, today: date | None = None) -> RuntimeRuleSet:
    report = validate_loaded(rulebase, today=today or date.today())
    if report.errors:
        raise RulebaseInvalidError(report.errors)
    chosen: list[tuple[LoadedRule, int]] = []
    for lr in rulebase.rules.values():
        version = served_version(lr.model)
        if version is None or version not in lr.contents or not _owner_approved(lr, version):
            continue
        chosen.append((lr, version))
    ids = {lr.rule_id for lr, _ in chosen}
    rules = tuple(sorted((_to_runtime(lr, v, ids) for lr, v in chosen), key=lambda r: r.rule_id))
    return RuntimeRuleSet(rules)


def load_runtime_rules(paths: RulebasePaths, *, today: date | None = None) -> RuntimeRuleSet:
    return build_runtime_rules(load_rulebase(paths), today=today)


__all__ = [
    "RuleLink",
    "RulebaseInvalidError",
    "RuntimeRule",
    "RuntimeRuleSet",
    "build_runtime_rules",
    "load_runtime_rules",
]
