"""Controlled vocabularies of the rule knowledge base (docs/rule-schema.md, data-model.md section 4.4)."""

from enum import StrEnum


class Namespace(StrEnum):
    """Rule namespaces. Traditions stay separate (CLAUDE.md rule 2); SHARED holds tradition-neutral mechanics."""

    PARASHARI = "PARASHARI"
    KP = "KP"
    JAIMINI = "JAIMINI"
    SHARED = "SHARED"


NAMESPACE_PREFIX: dict[Namespace, str] = {
    Namespace.PARASHARI: "PAR",
    Namespace.KP: "KP",
    Namespace.JAIMINI: "JAI",
    Namespace.SHARED: "SHR",
}
NAMESPACE_DIR: dict[Namespace, str] = {
    Namespace.PARASHARI: "parashari",
    Namespace.KP: "kp",
    Namespace.JAIMINI: "jaimini",
    Namespace.SHARED: "shared",
}


class RuleType(StrEnum):
    """Three kinds of record, kept apart (owner requirement 3)."""

    CALCULATION_RULE = "CALCULATION_RULE"  # how something is computed (formal spec)
    CALCULATION_CONVENTION = (
        "CALCULATION_CONVENTION"  # a profile setting choice, tied to a D-NNN decision
    )
    INTERPRETIVE_RULE = "INTERPRETIVE_RULE"  # what a computed configuration signifies


class Status(StrEnum):
    DRAFT = "DRAFT"  # working notes, may be incomplete
    PROVISIONAL = "PROVISIONAL"  # complete, cited, awaiting owner source approval
    VERIFIED = "VERIFIED"  # owner source-approved (NOT expert-validated)
    CONFLICTING_SOURCES = "CONFLICTING_SOURCES"  # sources disagree; records kept apart
    REJECTED = "REJECTED"  # owner rejected this version


class Actor(StrEnum):
    OWNER = "OWNER"
    CLAUDE_CODE = "CLAUDE_CODE"
    MODEL = "MODEL"
    INDEPENDENT_REVIEWER = "INDEPENDENT_REVIEWER"


class ReviewType(StrEnum):
    SOURCE_APPROVAL = "SOURCE_APPROVAL"
    DRAFT_REVIEW = "DRAFT_REVIEW"
    TECHNICAL_VALIDATION = "TECHNICAL_VALIDATION"
    INDEPENDENT_REVIEW = "INDEPENDENT_REVIEW"
    INDEPENDENT_CALCULATION = "INDEPENDENT_CALCULATION"


class Verdict(StrEnum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    CONFLICT_NOTED = "CONFLICT_NOTED"
    REJECT = "REJECT"


class RecordedVia(StrEnum):
    CLI_INTERACTIVE = (
        "CLI_INTERACTIVE"  # written by `jyotish rules approve` after a typed confirmation
    )
    FILE_EDIT = "FILE_EDIT"  # written by editing the YAML directly


class CitationRelation(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    COMMENTARY = "COMMENTARY"


class PassageReview(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"
    CORRECTED = "CORRECTED"


class RelationKind(StrEnum):
    ALTERNATIVE_READING = "ALTERNATIVE_READING"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    SUPERSEDES = "SUPERSEDES"
    DEPENDS_ON = "DEPENDS_ON"


class IndependentValidation(StrEnum):
    NONE = "NONE"
    RECORDED = "RECORDED"


class SettingKey(StrEnum):
    """Calculation settings that must come from a versioned profile (CLAUDE.md rule 4)."""

    AYANAMSHA = "ayanamsha"
    NODE = "node"
    HOUSE_SYSTEM = "house_system"
    KARAKA_SCHEME = "karaka_scheme"
    JAIMINI_DASHA_METHOD = "jaimini_dasha_method"
    DASHA_YEAR_DAYS = "dasha_year_days"
    BOUNDARY_RULE = "boundary_rule"
    VARGA_METHOD = "varga_method"


class Rights(StrEnum):
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    OWNED_COPY_PERSONAL_USE = "OWNED_COPY_PERSONAL_USE"
    LICENSED = "LICENSED"
    UNKNOWN = "UNKNOWN"


class Ownership(StrEnum):
    """Q-014: no book is assumed to be owned. Only the owner can move a source to OWNER_CONFIRMED."""

    UNCONFIRMED = "UNCONFIRMED"
    OWNER_CONFIRMED = "OWNER_CONFIRMED"


# Profile keys (architecture.md section 4). Profiles are separate objects; each belongs to one tradition.
PROFILE_NAMESPACE: dict[str, Namespace] = {
    "parashari-lahiri": Namespace.PARASHARI,
    "kp-krishnamurti": Namespace.KP,
    "jaimini-lahiri-7k": Namespace.JAIMINI,
    "jaimini-lahiri-8k": Namespace.JAIMINI,
}

# Which traditions each setting may apply to. `dasha_year_days` is Vimshottari-only (never Jaimini,
# CLAUDE.md rule 4); `karaka_scheme` and the Jaimini dasha method are Jaimini-only.
SETTING_NAMESPACES: dict[SettingKey, frozenset[Namespace]] = {
    SettingKey.AYANAMSHA: frozenset(Namespace),
    SettingKey.NODE: frozenset(Namespace),
    SettingKey.HOUSE_SYSTEM: frozenset(Namespace),
    SettingKey.BOUNDARY_RULE: frozenset(Namespace),
    SettingKey.VARGA_METHOD: frozenset({Namespace.PARASHARI, Namespace.SHARED}),
    SettingKey.DASHA_YEAR_DAYS: frozenset({Namespace.PARASHARI, Namespace.KP, Namespace.SHARED}),
    SettingKey.KARAKA_SCHEME: frozenset({Namespace.JAIMINI}),
    SettingKey.JAIMINI_DASHA_METHOD: frozenset({Namespace.JAIMINI}),
}
