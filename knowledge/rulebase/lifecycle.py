"""Rule lifecycle (docs/rule-schema.md section 4).

Status belongs to a *version*. Content is immutable once written (hash-checked), so the status of a version is
the `to` of its last lifecycle event, and every event is append-only audit. A new version starts again at
DRAFT or PROVISIONAL, so approval never carries over to changed text.
"""

from knowledge.rulebase.enums import Actor, Status
from knowledge.rulebase.models import LifecycleEvent, RuleFile

# from -> allowed targets. `None` is the start (first event of a version).
TRANSITIONS: dict[Status | None, frozenset[Status]] = {
    None: frozenset({Status.DRAFT, Status.PROVISIONAL}),
    Status.DRAFT: frozenset({Status.PROVISIONAL, Status.REJECTED}),
    Status.PROVISIONAL: frozenset({Status.VERIFIED, Status.CONFLICTING_SOURCES, Status.REJECTED}),
    Status.CONFLICTING_SOURCES: frozenset({Status.PROVISIONAL, Status.VERIFIED, Status.REJECTED}),
    Status.VERIFIED: frozenset({Status.REJECTED}),
    Status.REJECTED: frozenset(),
}

# Only the owner can verify or reject (CLAUDE.md: marking VERIFIED is the owner's SOURCE_APPROVAL, never a model's).
OWNER_ONLY_TARGETS: frozenset[Status] = frozenset({Status.VERIFIED, Status.REJECTED})
# Statuses a non-owner may record.
DRAFTING_ACTORS: frozenset[Actor] = frozenset({Actor.OWNER, Actor.CLAUDE_CODE, Actor.MODEL})
# A version that ever reached one of these must be complete (no longer a working draft).
COMPLETE_STATUSES: frozenset[Status] = frozenset(
    {Status.PROVISIONAL, Status.VERIFIED, Status.CONFLICTING_SOURCES}
)


def events_for(rule: RuleFile, version: int) -> list[LifecycleEvent]:
    return [event for event in rule.lifecycle if event.rule_version == version]


def status_of_version(rule: RuleFile, version: int) -> Status | None:
    """Status of one version: the `to` of its last event, or None if it has no event."""
    events = events_for(rule, version)
    return events[-1].to_status if events else None


def states_by_version(rule: RuleFile) -> dict[int, Status | None]:
    return {entry.version: status_of_version(rule, entry.version) for entry in rule.versions}


def latest_version(rule: RuleFile) -> int:
    return max(entry.version for entry in rule.versions)


def current_status(rule: RuleFile) -> Status | None:
    """Status of the latest version."""
    return status_of_version(rule, latest_version(rule))


def ever_complete(rule: RuleFile, version: int) -> bool:
    return any(event.to_status in COMPLETE_STATUSES for event in events_for(rule, version))


def served_version(rule: RuleFile) -> int | None:
    """Highest version currently VERIFIED: the only version runtime retrieval may serve.

    A newer DRAFT/PROVISIONAL/CONFLICTING version does not take an approved older version offline, but it is
    never served itself. A REJECTED newer version leaves the older approved one in place. (Open question Q-021.)
    """
    verified = [v for v, s in states_by_version(rule).items() if s is Status.VERIFIED]
    return max(verified) if verified else None
