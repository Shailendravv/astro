"""Pydantic models for rule records (docs/rule-schema.md).

The models check types and allowed keys only (`extra="forbid"`). Meaning checks (lifecycle, citations,
cross-record links) live in `validator.py` so the messages can say exactly what is wrong.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from knowledge.rulebase.enums import (
    Actor,
    CitationRelation,
    IndependentValidation,
    Namespace,
    PassageReview,
    RecordedVia,
    RelationKind,
    ReviewType,
    RuleType,
    SettingKey,
    Status,
    Verdict,
)


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


# ---------------------------------------------------------------- content pieces


class Citation(Base):
    citation_id: str  # "<source_id>:<locator>", e.g. SRC-EXAMPLE-V1:ch1:v2
    relation: CitationRelation
    quote: str = ""
    chapter: str | None = None
    page: str | None = None  # page as printed in the cited edition
    passage_review_status: PassageReview = PassageReview.UNREVIEWED
    note: str | None = None


class Relation(Base):
    kind: RelationKind
    target: str  # rule_id
    note: str | None = None


class Condition(Base):
    text: str
    fact_pattern: str | None = None  # optional fact_id pattern the retrieval layer can match


class ExceptionClause(Base):
    text: str
    citation_id: str | None = None


class Alternative(Base):
    value: str
    source_note: str | None = None


class Convention(Base):
    setting_key: SettingKey
    applies_to_profiles: list[str] = Field(default_factory=list)
    chosen_value: str | None = None
    alternatives: list[Alternative] = Field(default_factory=list)
    decision_ref: str  # D-NNN in docs/decisions.md


class ContentBase(Base):
    title: str = ""
    statement: str = ""
    citations: list[Citation] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    ambiguity_notes: list[str] = Field(default_factory=list)


class InterpretiveContent(ContentBase):
    conditions: list[Condition] = Field(default_factory=list)
    effect: str = ""
    exceptions: list[ExceptionClause] = Field(default_factory=list)
    requires_calculation_rules: list[str] = Field(default_factory=list)
    interpretation_notes: str | None = None


class CalculationContent(ContentBase):
    formal_spec: str = ""
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    uses_conventions: list[str] = Field(default_factory=list)  # CALCULATION_CONVENTION rule_ids
    method_id: str | None = None  # e.g. CHARA_KNRAO_<edition-key> (D-008)


class ConventionContent(ContentBase):
    convention: Convention | None = None


CONTENT_MODELS: dict[RuleType, type[ContentBase]] = {
    RuleType.INTERPRETIVE_RULE: InterpretiveContent,
    RuleType.CALCULATION_RULE: CalculationContent,
    RuleType.CALCULATION_CONVENTION: ConventionContent,
}


# ---------------------------------------------------------------- record pieces


class CreatedBy(Base):
    actor: Actor
    provider: str | None = None
    model_id: str | None = None  # exact ID as returned by the provider; required when actor = MODEL


class VersionEntry(Base):
    version: int = Field(ge=1)
    created: date
    created_by: CreatedBy
    change_note: str
    content: dict[str, Any]
    content_hash: str


class IndependentSource(Base):
    name: str
    version: str
    settings: str | dict[str, Any]


class Evidence(Base):
    citation_ids: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    independent_source: IndependentSource | None = None


class Review(Base):
    review_id: str
    rule_version: int = Field(ge=1)
    content_hash: str
    actor: Actor
    review_type: ReviewType
    verdict: Verdict
    date: date
    recorded_via: RecordedVia = RecordedVia.FILE_EDIT
    provider: str | None = None
    model_id: str | None = None
    reviewer_name: str | None = None
    stated_qualifications: str | None = None
    evidence: Evidence = Field(default_factory=Evidence)
    notes: str | None = None


class LifecycleEvent(Base):
    event_id: str
    rule_version: int = Field(ge=1)
    from_status: Status | None = Field(alias="from")
    to_status: Status = Field(alias="to")
    date: date
    actor: Actor
    recorded_via: RecordedVia = RecordedVia.FILE_EDIT
    reason: str | None = None
    review_id: str | None = None


class RuleFile(Base):
    schema_version: int
    rule_id: str
    namespace: Namespace
    rule_type: RuleType
    topic: str
    terms: list[str] = Field(default_factory=list)  # glossary keys
    independent_validation: IndependentValidation = IndependentValidation.NONE
    versions: list[VersionEntry] = Field(min_length=1)
    reviews: list[Review] = Field(default_factory=list)
    lifecycle: list[LifecycleEvent] = Field(min_length=1)
    implemented_in: list[str] = Field(default_factory=list)  # filled by tooling
    tests: list[str] = Field(default_factory=list)  # filled by tooling
