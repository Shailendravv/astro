"""Rule knowledge base validator (`jyotish rules validate`).

Every check has a stable code (see docs/rule-schema.md section 8). What it can and cannot prove:

- It proves the records are internally consistent: IDs, namespaces, versions and hashes, lifecycle order,
  that a VERIFIED version carries a version-bound owner approval, citations resolve to the catalogue,
  conflicts are kept as separate linked records, conventions match their decisions.
- It does NOT prove a rule is correct Jyotish, and it cannot prove *who* typed an approval. Authenticity
  of owner approvals rests on `jyotish rules approve` (interactive terminal only), the append-only history
  check against git, and the owner reviewing diffs (decisions.md D-031, Q-020).
"""

import re
from datetime import date

from knowledge.rulebase.enums import (
    NAMESPACE_DIR,
    NAMESPACE_PREFIX,
    PROFILE_NAMESPACE,
    SETTING_NAMESPACES,
    Actor,
    CitationRelation,
    IndependentValidation,
    Namespace,
    Ownership,
    PassageReview,
    RecordedVia,
    RelationKind,
    ReviewType,
    RuleType,
    SettingKey,
    Status,
    Verdict,
)
from knowledge.rulebase.findings import Finding, Report, error, warning
from knowledge.rulebase.hashing import version_hash
from knowledge.rulebase.lifecycle import (
    DRAFTING_ACTORS,
    OWNER_ONLY_TARGETS,
    TRANSITIONS,
    current_status,
    events_for,
    ever_complete,
    latest_version,
    served_version,
    states_by_version,
    status_of_version,
)
from knowledge.rulebase.loader import LoadedRule, Rulebase, RulebasePaths, load_rulebase
from knowledge.rulebase.models import (
    CalculationContent,
    ContentBase,
    ConventionContent,
    InterpretiveContent,
    LifecycleEvent,
    Review,
)
from knowledge.rulebase.sources import SOURCE_ID_PATTERN, source_id_of

RULE_ID_PATTERN = re.compile(r"^(PAR|KP|JAI|SHR)-([A-Z]{3})-(\d{4})$")
REVIEW_ID_PATTERN = re.compile(r"^R-\d{4}$")
EVENT_ID_PATTERN = re.compile(r"^E-\d{4}$")
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
CITATION_ID_PATTERN = re.compile(r"^SRC-[A-Z0-9]+(?:-[A-Z0-9]+)*:[A-Za-z0-9._:-]+$")
DECISION_REF_PATTERN = re.compile(r"^D-\d{3}$")
METHOD_ID_PATTERN = re.compile(r"^CHARA_KNRAO_[A-Za-z0-9]+$")
TERM_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
QUOTE_MAX_CHARS = 500  # keep quoted book text short: books are never committed (security.md, D-011)
MODEL_LIKE_NAMES = ("claude", "qwen", "groq", "gpt", "llama", "opus", "sonnet", "haiku")
CONFLICT_KINDS = (RelationKind.CONFLICTS_WITH, RelationKind.ALTERNATIVE_READING)

ALLOWED_REVIEW_TYPES: dict[Actor, frozenset[ReviewType]] = {
    Actor.OWNER: frozenset({ReviewType.SOURCE_APPROVAL}),
    Actor.CLAUDE_CODE: frozenset({ReviewType.DRAFT_REVIEW, ReviewType.TECHNICAL_VALIDATION}),
    Actor.MODEL: frozenset({ReviewType.DRAFT_REVIEW, ReviewType.TECHNICAL_VALIDATION}),
    Actor.INDEPENDENT_REVIEWER: frozenset(
        {ReviewType.INDEPENDENT_REVIEW, ReviewType.INDEPENDENT_CALCULATION}
    ),
}
INDEPENDENT_TYPES = frozenset({ReviewType.INDEPENDENT_REVIEW, ReviewType.INDEPENDENT_CALCULATION})


def validate_rulebase(paths: RulebasePaths, *, today: date | None = None) -> Report:
    return validate_loaded(load_rulebase(paths), today=today or date.today())


def validate_loaded(rulebase: Rulebase, *, today: date) -> Report:
    checker = _Checker(rulebase, today)
    checker.run()
    return Report(
        findings=checker.findings,
        rules_checked=len(rulebase.rules),
        sources_checked=rulebase.source_files_seen,
    )


class _Checker:
    def __init__(self, rulebase: Rulebase, today: date) -> None:
        self.rb = rulebase
        self.today = today
        self.findings: list[Finding] = list(rulebase.findings)

    # ------------------------------------------------------------ reporting helpers
    def err(self, code: str, message: str, lr: LoadedRule) -> None:
        self.findings.append(error(code, message, rule_id=lr.rule_id, file=lr.rel))

    def warn(self, code: str, message: str, lr: LoadedRule) -> None:
        self.findings.append(warning(code, message, rule_id=lr.rule_id, file=lr.rel))

    # ------------------------------------------------------------ driver
    def run(self) -> None:
        for lr in self.rb.rules.values():
            self.identity(lr)
            self.versions(lr)
            self.lifecycle(lr)
            self.reviews(lr)
            for entry in lr.model.versions:
                self.content(lr, entry.version)
            self.verified_versions(lr)
            self.independent(lr)
        self.relations()
        self.dependencies()

    # ------------------------------------------------------------ identity
    def identity(self, lr: LoadedRule) -> None:
        rule = lr.model
        if rule.schema_version != 1:
            self.err("FILE-SCHEMA-VERSION", f"unsupported schema_version {rule.schema_version}", lr)
        match = RULE_ID_PATTERN.match(rule.rule_id)
        if not match:
            self.err(
                "RULE-ID-FORMAT",
                f"rule_id {rule.rule_id!r} must match (PAR|KP|JAI|SHR)-XXX-NNNN",
                lr,
            )
        elif match.group(1) != NAMESPACE_PREFIX[rule.namespace]:
            self.err(
                "RULE-ID-NAMESPACE",
                f"prefix {match.group(1)} does not belong to namespace {rule.namespace.value} "
                f"(expected {NAMESPACE_PREFIX[rule.namespace]})",
                lr,
            )
        if lr.rel.split("/")[0] != NAMESPACE_DIR[rule.namespace]:
            self.err(
                "RULE-DIR-NAMESPACE",
                f"file is in {lr.rel.split('/')[0]!r} but namespace is {rule.namespace.value} "
                f"(expected directory {NAMESPACE_DIR[rule.namespace]!r})",
                lr,
            )
        if lr.rel.split("/")[-1] != f"{rule.rule_id}.yaml":
            self.err("RULE-FILENAME", f"file name must be {rule.rule_id}.yaml", lr)
        for term in rule.terms:
            if not TERM_PATTERN.match(term):
                self.err("TERM-FORMAT", f"glossary key {term!r} must be lower_snake_case", lr)
        vocabulary = self.rb.vocabulary
        if vocabulary:
            topic = vocabulary.get(rule.topic)
            if topic is None:
                self.err("TOPIC-UNKNOWN", f"topic {rule.topic!r} is not in the vocabulary", lr)
            else:
                if match and match.group(2) != topic.code:
                    self.err(
                        "TOPIC-CODE",
                        f"rule_id topic code {match.group(2)} does not match topic {rule.topic!r} ({topic.code})",
                        lr,
                    )
                if rule.namespace not in topic.namespaces:
                    self.err(
                        "TOPIC-NAMESPACE",
                        f"topic {rule.topic!r} is not allowed in {rule.namespace.value}",
                        lr,
                    )

    # ------------------------------------------------------------ versions
    def versions(self, lr: LoadedRule) -> None:
        rule = lr.model
        numbers = [entry.version for entry in rule.versions]
        if numbers != list(range(1, len(numbers) + 1)):
            self.err("VERSION-SEQUENCE", f"versions must be 1..n in order, found {numbers}", lr)
        previous = None
        for entry in rule.versions:
            if not HASH_PATTERN.match(entry.content_hash):
                self.err(
                    "VERSION-HASH-FORMAT",
                    f"version {entry.version}: content_hash must be sha256:<64 hex>",
                    lr,
                )
            elif entry.content_hash != version_hash(rule.rule_id, entry.version, entry.content):
                self.err(
                    "VERSION-HASH",
                    f"version {entry.version}: content_hash does not match the content. Content of a recorded "
                    "version is immutable: create a new version instead (then run `jyotish rules seal`)",
                    lr,
                )
            if not entry.change_note.strip():
                self.err(
                    "VERSION-CHANGE-NOTE", f"version {entry.version}: change_note is empty", lr
                )
            if entry.created > self.today:
                self.err(
                    "VERSION-DATE-FUTURE",
                    f"version {entry.version}: created date is in the future",
                    lr,
                )
            if entry.created_by.actor is Actor.INDEPENDENT_REVIEWER:
                self.err(
                    "VERSION-ACTOR",
                    f"version {entry.version}: an independent reviewer cannot author a version",
                    lr,
                )
            if entry.created_by.actor is Actor.MODEL and not (
                entry.created_by.provider and entry.created_by.model_id
            ):
                self.err(
                    "VERSION-ACTOR",
                    f"version {entry.version}: a MODEL author needs provider and the exact model_id",
                    lr,
                )
            if previous is not None:
                if entry.created < previous.created:
                    self.err(
                        "VERSION-DATE-ORDER",
                        f"version {entry.version} is dated before version {previous.version}",
                        lr,
                    )
                if entry.content == previous.content:
                    self.warn(
                        "VERSION-NOOP",
                        f"version {entry.version} has the same content as version {previous.version}",
                        lr,
                    )
            previous = entry

    # ------------------------------------------------------------ lifecycle
    def _review(self, lr: LoadedRule, review_id: str | None) -> Review | None:
        return next((r for r in lr.model.reviews if r.review_id == review_id), None)

    def lifecycle(self, lr: LoadedRule) -> None:
        rule = lr.model
        known_versions = {entry.version: entry for entry in rule.versions}
        last_date: date | None = None
        for index, event in enumerate(rule.lifecycle, start=1):
            if event.event_id != f"E-{index:04d}" or not EVENT_ID_PATTERN.match(event.event_id):
                self.err(
                    "EVENT-ID",
                    f"event #{index} must have id E-{index:04d}, found {event.event_id!r}",
                    lr,
                )
            if event.rule_version not in known_versions:
                self.err(
                    "EVENT-VERSION",
                    f"{event.event_id}: version {event.rule_version} does not exist",
                    lr,
                )
            if last_date is not None and event.date < last_date:
                self.err(
                    "EVENT-DATE-ORDER", f"{event.event_id} is dated before the previous event", lr
                )
            if event.date > self.today:
                self.err("EVENT-DATE-FUTURE", f"{event.event_id}: date is in the future", lr)
            last_date = event.date

        for entry in rule.versions:
            events = events_for(rule, entry.version)
            if not events:
                self.err("EVENT-MISSING", f"version {entry.version} has no lifecycle event", lr)
                continue
            previous: Status | None = None
            for event in events:
                self.event(lr, entry.version, event, previous)
                previous = event.to_status

    def event(
        self, lr: LoadedRule, version: int, event: LifecycleEvent, previous: Status | None
    ) -> None:
        target = event.to_status
        label = event.event_id
        if event.from_status != previous:
            self.err(
                "EVENT-FROM",
                f"{label}: 'from' is {event.from_status}, but the version was {previous}",
                lr,
            )
        if target not in TRANSITIONS.get(previous, frozenset()):
            self.err(
                "EVENT-TRANSITION",
                f"{label}: {previous.value if previous else 'start'} -> {target.value} is not an allowed transition",
                lr,
            )
        if target in OWNER_ONLY_TARGETS:
            if (
                event.actor is not Actor.OWNER
                or event.recorded_via is not RecordedVia.CLI_INTERACTIVE
            ):
                self.err(
                    "EVENT-OWNER-ONLY",
                    f"{label}: {target.value} can only be recorded by the owner through "
                    "`jyotish rules approve` (actor OWNER, recorded_via CLI_INTERACTIVE)",
                    lr,
                )
            self.approval(lr, version, event)
            if target is Status.REJECTED and not (event.reason or "").strip():
                self.err("EVENT-REASON", f"{label}: a rejection needs a reason", lr)
        elif event.actor not in DRAFTING_ACTORS:
            self.err(
                "EVENT-ACTOR",
                f"{label}: actor {event.actor.value} cannot record {target.value}",
                lr,
            )
        if target is Status.CONFLICTING_SOURCES:
            if not (event.reason or "").strip():
                self.err("EVENT-REASON", f"{label}: CONFLICTING_SOURCES needs a reason", lr)
            content = lr.contents.get(version)
            if content is not None and not any(r.kind in CONFLICT_KINDS for r in content.relations):
                self.err(
                    "EVENT-CONFLICT-RELATION",
                    f"{label}: CONFLICTING_SOURCES requires a CONFLICTS_WITH or ALTERNATIVE_READING relation "
                    "to the other record (conflicts are kept as separate linked records)",
                    lr,
                )
        if (
            previous is Status.CONFLICTING_SOURCES
            and target is Status.PROVISIONAL
            and not (event.reason or "").strip()
        ):
            self.err("EVENT-REASON", f"{label}: leaving CONFLICTING_SOURCES needs a reason", lr)

    def approval(self, lr: LoadedRule, version: int, event: LifecycleEvent) -> None:
        label = event.event_id
        review = self._review(lr, event.review_id)
        if review is None:
            self.err(
                "EVENT-APPROVAL",
                f"{label}: {event.to_status.value} needs a review_id pointing to an owner review",
                lr,
            )
            return
        entry = next((e for e in lr.model.versions if e.version == version), None)
        wanted = Verdict.APPROVE if event.to_status is Status.VERIFIED else Verdict.REJECT
        problems = []
        if review.actor is not Actor.OWNER or review.review_type is not ReviewType.SOURCE_APPROVAL:
            problems.append("must be an OWNER SOURCE_APPROVAL review")
        if review.recorded_via is not RecordedVia.CLI_INTERACTIVE:
            problems.append("must be recorded via CLI_INTERACTIVE")
        if review.verdict is not wanted:
            problems.append(f"verdict must be {wanted.value}")
        if review.rule_version != version:
            problems.append(f"is for version {review.rule_version}, not {version}")
        if entry is not None and review.content_hash != entry.content_hash:
            problems.append(
                "content_hash differs from the version it is being applied to (approval is version-bound)"
            )
        if review.date > event.date:
            problems.append("is dated after the event that relies on it")
        for problem in problems:
            self.err("EVENT-APPROVAL", f"{label}: review {review.review_id} {problem}", lr)

    # ------------------------------------------------------------ reviews
    def reviews(self, lr: LoadedRule) -> None:
        rule = lr.model
        seen: set[str] = set()
        versions = {entry.version: entry for entry in rule.versions}
        for review in rule.reviews:
            rid = review.review_id
            if not REVIEW_ID_PATTERN.match(rid) or rid in seen:
                self.err("REVIEW-ID", f"review id {rid!r} must be unique and look like R-0001", lr)
            seen.add(rid)
            entry = versions.get(review.rule_version)
            if entry is None:
                self.err(
                    "REVIEW-VERSION", f"{rid}: version {review.rule_version} does not exist", lr
                )
            else:
                if review.content_hash != entry.content_hash:
                    self.err(
                        "REVIEW-HASH",
                        f"{rid}: content_hash does not match version {review.rule_version}",
                        lr,
                    )
                if review.date < entry.created:
                    self.err(
                        "REVIEW-DATE",
                        f"{rid}: dated before version {review.rule_version} was written",
                        lr,
                    )
            if review.date > self.today:
                self.err("REVIEW-DATE", f"{rid}: date is in the future", lr)
            if review.review_type not in ALLOWED_REVIEW_TYPES[review.actor]:
                self.err(
                    "REVIEW-ACTOR-TYPE",
                    f"{rid}: actor {review.actor.value} cannot give a {review.review_type.value}",
                    lr,
                )
            if (
                review.actor is Actor.OWNER
                and review.recorded_via is not RecordedVia.CLI_INTERACTIVE
            ):
                self.err(
                    "REVIEW-OWNER-VIA",
                    f"{rid}: owner reviews must be recorded via `jyotish rules approve`",
                    lr,
                )
            if review.actor is Actor.MODEL and not (review.provider and review.model_id):
                self.err(
                    "REVIEW-MODEL",
                    f"{rid}: a MODEL review needs provider and the exact model_id",
                    lr,
                )
            if review.review_type is ReviewType.INDEPENDENT_REVIEW and not (
                review.reviewer_name and review.stated_qualifications
            ):
                self.err(
                    "REVIEW-INDEPENDENT",
                    f"{rid}: needs reviewer_name and stated_qualifications (as stated, never inferred)",
                    lr,
                )
            if (
                review.review_type is ReviewType.INDEPENDENT_CALCULATION
                and review.evidence.independent_source is None
            ):
                self.err(
                    "REVIEW-INDEPENDENT",
                    f"{rid}: needs evidence.independent_source (name, version, settings)",
                    lr,
                )
            if review.actor is Actor.INDEPENDENT_REVIEWER:
                name = (review.reviewer_name or "").lower()
                if (
                    review.review_type is ReviewType.INDEPENDENT_CALCULATION
                    and review.evidence.independent_source
                ):
                    name = review.evidence.independent_source.name.lower()
                if any(model in name for model in MODEL_LIKE_NAMES):
                    self.err(
                        "REVIEW-INDEPENDENT-NAME",
                        f"{rid}: a model or drafting tool cannot be recorded as an independent reviewer",
                        lr,
                    )
            if review.review_type is ReviewType.TECHNICAL_VALIDATION and not review.evidence.tests:
                self.err("REVIEW-EVIDENCE", f"{rid}: TECHNICAL_VALIDATION needs evidence.tests", lr)
            if (
                review.review_type is ReviewType.SOURCE_APPROVAL
                and review.verdict is Verdict.APPROVE
            ):
                content = lr.contents.get(review.rule_version)
                cited = {c.citation_id for c in content.citations} if content else set()
                if not review.evidence.citation_ids:
                    self.err(
                        "REVIEW-EVIDENCE",
                        f"{rid}: a source approval must list the citation_ids the owner reviewed",
                        lr,
                    )
                elif content is not None and not set(review.evidence.citation_ids) <= cited:
                    self.err(
                        "REVIEW-EVIDENCE",
                        f"{rid}: evidence lists citations that the version does not contain",
                        lr,
                    )

    # ------------------------------------------------------------ content
    def content(self, lr: LoadedRule, version: int) -> None:
        content = lr.contents.get(version)
        if content is None:
            return
        rule = lr.model
        complete = ever_complete(rule, version)
        seen: set[str] = set()
        for citation in content.citations:
            cid = citation.citation_id
            if not CITATION_ID_PATTERN.match(cid):
                self.err(
                    "CITATION-FORMAT",
                    f"v{version}: citation_id {cid!r} must look like SRC-XXX:locator",
                    lr,
                )
                continue
            if cid in seen:
                self.err("CITATION-DUPLICATE", f"v{version}: citation {cid} listed twice", lr)
            seen.add(cid)
            if len(citation.quote) > QUOTE_MAX_CHARS:
                self.err(
                    "CITATION-QUOTE-LONG",
                    f"v{version}: quote for {cid} exceeds {QUOTE_MAX_CHARS} characters",
                    lr,
                )
            source_id = source_id_of(cid)
            if not SOURCE_ID_PATTERN.match(source_id) or source_id not in self.rb.sources:
                (self.err if complete else self.warn)(
                    "CITATION-SOURCE",
                    f"v{version}: source {source_id} is not in the source catalogue",
                    lr,
                )
        for relation in content.relations:
            if not RULE_ID_PATTERN.match(relation.target):
                self.err(
                    "REL-TARGET-FORMAT",
                    f"v{version}: relation target {relation.target!r} is not a rule_id",
                    lr,
                )

        if any(c.relation is CitationRelation.CONTRADICTS for c in content.citations) and not any(
            r.kind in CONFLICT_KINDS for r in content.relations
        ):
            self.err(
                "CONFLICT-NOT-PRESERVED",
                f"v{version}: a source contradicts this rule, but no CONFLICTS_WITH/ALTERNATIVE_READING "
                "relation links the record that reflects it. Disagreeing sources become separate linked records",
                lr,
            )
        if complete:
            self.complete(lr, version, content)

        if isinstance(content, ConventionContent):
            self.convention(lr, version, content)
        if isinstance(content, CalculationContent) and content.method_id is not None:
            self.method(lr, version, content, complete)

    def complete(self, lr: LoadedRule, version: int, content: ContentBase) -> None:
        if not content.title.strip():
            self.err("CONTENT-INCOMPLETE", f"v{version}: title is empty", lr)
        if len(content.statement.strip()) < 10:
            self.err("CONTENT-INCOMPLETE", f"v{version}: statement is missing or too short", lr)
        supports = [c for c in content.citations if c.relation is CitationRelation.SUPPORTS]
        if not supports:
            self.err(
                "CITATION-NO-SUPPORT",
                f"v{version}: needs at least one SUPPORTS citation (source before rule)",
                lr,
            )
        for citation in supports:
            if not citation.quote.strip():
                self.err(
                    "CITATION-QUOTE-MISSING",
                    f"v{version}: {citation.citation_id} needs a quote",
                    lr,
                )
            if not (citation.page or citation.chapter):
                self.err(
                    "CITATION-LOCATOR",
                    f"v{version}: {citation.citation_id} needs a page or chapter in the cited edition",
                    lr,
                )
        if isinstance(content, InterpretiveContent):
            if not content.conditions:
                self.err(
                    "CONTENT-INCOMPLETE",
                    f"v{version}: an interpretive rule needs at least one condition",
                    lr,
                )
            if not content.effect.strip():
                self.err(
                    "CONTENT-INCOMPLETE", f"v{version}: an interpretive rule needs an effect", lr
                )
        elif isinstance(content, CalculationContent):
            if not content.formal_spec.strip():
                self.err(
                    "CONTENT-INCOMPLETE", f"v{version}: a calculation rule needs a formal_spec", lr
                )
            if not content.outputs:
                self.err(
                    "CONTENT-INCOMPLETE",
                    f"v{version}: a calculation rule needs at least one output",
                    lr,
                )
        elif isinstance(content, ConventionContent):
            convention = content.convention
            if convention is None:
                self.err(
                    "CONTENT-INCOMPLETE",
                    f"v{version}: a convention rule needs a 'convention' block",
                    lr,
                )
            else:
                if not convention.applies_to_profiles:
                    self.err(
                        "CONTENT-INCOMPLETE",
                        f"v{version}: convention must list applies_to_profiles",
                        lr,
                    )
                if not convention.chosen_value and len(convention.alternatives) < 2:
                    self.err(
                        "CONTENT-INCOMPLETE",
                        f"v{version}: give chosen_value, or at least two alternatives",
                        lr,
                    )

    def convention(self, lr: LoadedRule, version: int, content: ConventionContent) -> None:
        convention = content.convention
        if convention is None:
            return
        if not DECISION_REF_PATTERN.match(convention.decision_ref):
            self.err(
                "CONV-DECISION-FORMAT",
                f"v{version}: decision_ref {convention.decision_ref!r} must look like D-003",
                lr,
            )
        elif self.rb.decisions is None:
            self.err(
                "CONV-DECISIONS-MISSING",
                "docs/decisions.md not found: cannot check decision_ref",
                lr,
            )
        elif convention.decision_ref not in self.rb.decisions:
            self.err(
                "CONV-DECISION-UNKNOWN",
                f"v{version}: {convention.decision_ref} is not in docs/decisions.md",
                lr,
            )
        namespace = lr.model.namespace
        allowed = SETTING_NAMESPACES[convention.setting_key]
        if namespace not in allowed:
            self.err(
                "CONV-SETTING-SCOPE",
                f"v{version}: setting {convention.setting_key.value!r} does not apply to namespace {namespace.value} "
                f"(allowed: {sorted(n.value for n in allowed)})",
                lr,
            )
        for profile in convention.applies_to_profiles:
            owner = PROFILE_NAMESPACE.get(profile)
            if owner is None:
                self.err("CONV-PROFILE-UNKNOWN", f"v{version}: unknown profile key {profile!r}", lr)
                continue
            if namespace is not Namespace.SHARED and owner is not namespace:
                self.err(
                    "CONV-PROFILE-NAMESPACE",
                    f"v{version}: profile {profile!r} belongs to {owner.value}, not {namespace.value} (profiles are separate objects)",
                    lr,
                )
            if owner not in allowed:
                self.err(
                    "CONV-SETTING-SCOPE",
                    f"v{version}: setting {convention.setting_key.value!r} must not apply to profile {profile!r}",
                    lr,
                )

    def method(
        self, lr: LoadedRule, version: int, content: CalculationContent, complete: bool
    ) -> None:
        """D-008 / CLAUDE.md: K.N. Rao Chara Dasha rules must name the exact edition they cite."""
        method_id = content.method_id or ""
        if not METHOD_ID_PATTERN.match(method_id):
            self.err(
                "METHOD-ID",
                f"v{version}: method_id {method_id!r} must look like CHARA_KNRAO_<edition-key>",
                lr,
            )
        if lr.model.namespace is not Namespace.JAIMINI:
            self.err(
                "METHOD-NAMESPACE",
                f"v{version}: Chara Dasha method rules belong to the JAIMINI namespace",
                lr,
            )
        if complete:
            for citation in content.citations:
                if citation.relation is not CitationRelation.SUPPORTS:
                    continue
                source = self.rb.sources.get(source_id_of(citation.citation_id))
                if source is not None and not (source.edition and source.publisher and source.year):
                    self.err(
                        "CHARA-EDITION",
                        f"v{version}: {source.source_id} must record exact edition, publisher and year before a Chara Dasha rule cites it (D-008, Q-008)",
                        lr,
                    )

    # ------------------------------------------------------------ VERIFIED preconditions
    def verified_versions(self, lr: LoadedRule) -> None:
        rule = lr.model
        for version, status in states_by_version(rule).items():
            if status is not Status.VERIFIED:
                continue
            content = lr.contents.get(version)
            if content is None:
                continue
            supports = [c for c in content.citations if c.relation is CitationRelation.SUPPORTS]
            event = next(
                (e for e in reversed(events_for(rule, version)) if e.to_status is Status.VERIFIED),
                None,
            )
            approval = self._review(lr, event.review_id) if event else None
            approved_ids = set(approval.evidence.citation_ids) if approval else set()
            reviewed = [
                c for c in supports if c.passage_review_status is not PassageReview.UNREVIEWED
            ]
            if not reviewed:
                self.err(
                    "VERIFIED-PASSAGE-UNREVIEWED",
                    f"v{version}: VERIFIED needs a SUPPORTS citation whose passage has been reviewed",
                    lr,
                )
            elif approval is not None and not any(c.citation_id in approved_ids for c in reviewed):
                self.err(
                    "VERIFIED-EVIDENCE",
                    f"v{version}: the owner's approval does not cover any reviewed SUPPORTS citation",
                    lr,
                )
            for citation in supports:
                source = self.rb.sources.get(source_id_of(citation.citation_id))
                if source is None:
                    continue
                if (
                    source.ownership is not Ownership.OWNER_CONFIRMED
                    and source.rights.value != "PUBLIC_DOMAIN"
                ):
                    self.err(
                        "VERIFIED-SOURCE-OWNERSHIP",
                        f"v{version}: {source.source_id} is not owner-confirmed or public domain (Q-014: no book is assumed to be owned)",
                        lr,
                    )
                if not source.edition:
                    self.err(
                        "VERIFIED-SOURCE-EDITION",
                        f"v{version}: {source.source_id} has no recorded edition",
                        lr,
                    )
            if isinstance(content, ConventionContent) and content.convention is not None:
                convention = content.convention
                if not convention.chosen_value:
                    self.err(
                        "VERIFIED-NO-VALUE",
                        f"v{version}: a VERIFIED convention must state its chosen_value",
                        lr,
                    )
                decisions = self.rb.decisions or {}
                decision = decisions.get(convention.decision_ref)
                if decision is not None and not decision.accepted:
                    self.err(
                        "VERIFIED-DECISION-NOT-ACCEPTED",
                        f"v{version}: {convention.decision_ref} is '{decision.status_text}', not ACCEPTED. "
                        "Conventions stay PROVISIONAL until the owner accepts the decision",
                        lr,
                    )

    # ------------------------------------------------------------ independent validation
    def independent(self, lr: LoadedRule) -> None:
        rule = lr.model
        latest = next(e for e in rule.versions if e.version == latest_version(rule))
        recorded = any(
            r.review_type in INDEPENDENT_TYPES
            and r.verdict is Verdict.APPROVE
            and r.rule_version == latest.version
            and r.content_hash == latest.content_hash
            for r in rule.reviews
        )
        derived = IndependentValidation.RECORDED if recorded else IndependentValidation.NONE
        if rule.independent_validation is not derived:
            self.err(
                "IND-MISMATCH",
                f"independent_validation is {rule.independent_validation.value} but the reviews imply {derived.value} "
                "(it is RECORDED only when an approving independent review or calculation of the latest version exists; never assumed)",
                lr,
            )

    # ------------------------------------------------------------ cross-record checks
    def latest_content(self, lr: LoadedRule) -> ContentBase | None:
        return lr.contents.get(latest_version(lr.model))

    def edges(self, lr: LoadedRule, content: ContentBase) -> list[tuple[str, str]]:
        """(kind, target) dependency edges: typed lists plus DEPENDS_ON relations."""
        found: list[tuple[str, str]] = []
        if isinstance(content, CalculationContent):
            found += [("uses_conventions", t) for t in content.uses_conventions]
        if isinstance(content, InterpretiveContent):
            found += [("requires_calculation_rules", t) for t in content.requires_calculation_rules]
        found += [
            ("DEPENDS_ON", r.target) for r in content.relations if r.kind is RelationKind.DEPENDS_ON
        ]
        return found

    def relations(self) -> None:
        rules = self.rb.rules
        for lr in rules.values():
            content = self.latest_content(lr)
            if content is None:
                continue
            ns = lr.model.namespace
            seen: set[tuple[RelationKind, str]] = set()
            for relation in content.relations:
                key = (relation.kind, relation.target)
                if key in seen:
                    self.err(
                        "REL-DUPLICATE",
                        f"relation {relation.kind.value} -> {relation.target} listed twice",
                        lr,
                    )
                seen.add(key)
                if not RULE_ID_PATTERN.match(relation.target):
                    continue  # reported by content()
                if relation.target == lr.rule_id:
                    self.err("REL-SELF", "a rule cannot relate to itself", lr)
                    continue
                target = rules.get(relation.target)
                if target is None:
                    self.err(
                        "REL-TARGET-UNKNOWN",
                        f"{relation.kind.value} target {relation.target} does not exist",
                        lr,
                    )
                    continue
                tns = target.model.namespace
                if relation.kind is RelationKind.DEPENDS_ON:
                    if tns is not ns and tns is not Namespace.SHARED:
                        self.err(
                            "REL-CROSS-TRADITION",
                            f"DEPENDS_ON {relation.target}: {ns.value} rules may depend only on their own namespace or SHARED (CLAUDE.md rule 2)",
                            lr,
                        )
                    if ns is Namespace.SHARED and tns is not Namespace.SHARED:
                        self.err(
                            "REL-CROSS-TRADITION",
                            f"SHARED rules may depend only on SHARED rules, not {relation.target}",
                            lr,
                        )
                elif relation.kind is RelationKind.SUPERSEDES:
                    if tns is not ns:
                        self.err(
                            "REL-SUPERSEDES-NAMESPACE",
                            f"SUPERSEDES {relation.target}: must stay inside {ns.value}",
                            lr,
                        )
                    if current_status(target.model) is not Status.REJECTED:
                        self.err(
                            "REL-SUPERSEDES-TARGET",
                            f"{relation.target} must be REJECTED by the owner before it can be superseded",
                            lr,
                        )
                    if not (relation.note or "").strip():
                        self.err(
                            "REL-NOTE",
                            f"SUPERSEDES {relation.target} needs a note giving the reason",
                            lr,
                        )
                else:  # CONFLICTS_WITH / ALTERNATIVE_READING
                    if len((relation.note or "").strip()) < 10:
                        self.err(
                            "REL-NOTE",
                            f"{relation.kind.value} {relation.target} needs a note explaining how the records differ",
                            lr,
                        )
                    other = self.latest_content(target)
                    if other is not None and not any(
                        r.kind is relation.kind and r.target == lr.rule_id for r in other.relations
                    ):
                        self.err(
                            "REL-ASYMMETRIC",
                            f"{relation.kind.value} {relation.target}: the other record must link back with the same kind",
                            lr,
                        )
            self.typed_links(lr, content)

    def typed_links(self, lr: LoadedRule, content: ContentBase) -> None:
        rules = self.rb.rules
        ns = lr.model.namespace
        wanted: tuple[str, RuleType] | None = None
        targets: list[str] = []
        if isinstance(content, CalculationContent):
            wanted, targets = (
                ("uses_conventions", RuleType.CALCULATION_CONVENTION),
                content.uses_conventions,
            )
        elif isinstance(content, InterpretiveContent):
            wanted, targets = (
                ("requires_calculation_rules", RuleType.CALCULATION_RULE),
                content.requires_calculation_rules,
            )
        if wanted is None:
            return
        field_name, wanted_type = wanted
        for target_id in targets:
            target = rules.get(target_id)
            if target is None:
                self.err("TYPE-LINK-UNKNOWN", f"{field_name}: {target_id} does not exist", lr)
                continue
            if target.model.rule_type is not wanted_type:
                self.err(
                    "TYPE-LINK",
                    f"{field_name}: {target_id} is a {target.model.rule_type.value}, expected {wanted_type.value}",
                    lr,
                )
            tns = target.model.namespace
            if tns is not ns and tns is not Namespace.SHARED:
                self.err(
                    "REL-CROSS-TRADITION",
                    f"{field_name}: {target_id} belongs to {tns.value}; rules never borrow from another tradition",
                    lr,
                )
        # karaka scheme and Jaimini dasha method are independent settings (D-007, Q-007)
        settings = {t: self.setting_of(rules.get(t)) for t in targets}
        if (
            SettingKey.KARAKA_SCHEME in settings.values()
            and SettingKey.JAIMINI_DASHA_METHOD in settings.values()
        ):
            self.warn(
                "CONV-COUPLING-CALC",
                "this rule uses both a karaka-scheme and a Jaimini-dasha-method convention. They are independent (Q-007): keep this only if a cited source states the coupling",
                lr,
            )

    @staticmethod
    def setting_of(lr: LoadedRule | None) -> SettingKey | None:
        if lr is None or lr.model.rule_type is not RuleType.CALCULATION_CONVENTION:
            return None
        content = lr.contents.get(latest_version(lr.model))
        if isinstance(content, ConventionContent) and content.convention is not None:
            return content.convention.setting_key
        return None

    def dependencies(self) -> None:
        rules = self.rb.rules
        graph: dict[str, list[str]] = {}
        for rule_id, lr in rules.items():
            content = self.latest_content(lr)
            graph[rule_id] = [t for _, t in self.edges(lr, content)] if content else []
            graph[rule_id] = [t for t in graph[rule_id] if t in rules]
        # convention <-> convention coupling between karaka scheme and dasha method
        for rule_id, targets in graph.items():
            a = self.setting_of(rules[rule_id])
            for linked in targets:
                b = self.setting_of(rules[linked])
                if {a, b} == {SettingKey.KARAKA_SCHEME, SettingKey.JAIMINI_DASHA_METHOD}:
                    self.err(
                        "CONV-COUPLING",
                        f"{rule_id} -> {linked}: karaka_scheme and jaimini_dasha_method are independent settings (D-007, Q-007)",
                        rules[rule_id],
                    )
        # cycles
        state: dict[str, int] = {}
        reported: set[str] = set()

        def visit(node: str, trail: list[str]) -> None:
            state[node] = 1
            for nxt in graph.get(node, []):
                if state.get(nxt) == 1:
                    cycle = [*trail[trail.index(nxt) :], nxt] if nxt in trail else [node, nxt]
                    key = "->".join(sorted(set(cycle)))
                    if key not in reported:
                        reported.add(key)
                        self.err(
                            "DEP-CYCLE", f"dependency cycle: {' -> '.join(cycle)}", rules[node]
                        )
                elif state.get(nxt) is None:
                    visit(nxt, [*trail, nxt])
            state[node] = 2

        for node in graph:
            if state.get(node) is None:
                visit(node, [node])
        # a served (VERIFIED) rule may not rest on rules that are not themselves VERIFIED
        for lr in rules.values():
            served = served_version(lr.model)
            if served is None:
                continue
            content = lr.contents.get(served)
            if content is None:
                continue
            for _, target_id in self.edges(lr, content):
                target = rules.get(target_id)
                if target is not None and served_version(target.model) is None:
                    self.err(
                        "DEP-UNVERIFIED",
                        f"VERIFIED v{served} depends on {target_id}, which has no VERIFIED version "
                        f"(status {status_of_version(target.model, latest_version(target.model))})",
                        lr,
                    )
