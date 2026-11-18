"""Rule knowledge base: schema, validator, lifecycle, approval, append-only history, runtime retrieval gate.

Reference: docs/rule-schema.md. Decision: docs/decisions.md D-031.
"""

from knowledge.rulebase.findings import Finding, Report, Severity
from knowledge.rulebase.loader import RulebasePaths, load_rulebase
from knowledge.rulebase.retrieval import (
    RulebaseInvalidError,
    RuntimeRule,
    RuntimeRuleSet,
    load_runtime_rules,
)
from knowledge.rulebase.validator import validate_rulebase

__all__ = [
    "Finding",
    "Report",
    "RulebaseInvalidError",
    "RulebasePaths",
    "RuntimeRule",
    "RuntimeRuleSet",
    "Severity",
    "load_rulebase",
    "load_runtime_rules",
    "validate_rulebase",
]
