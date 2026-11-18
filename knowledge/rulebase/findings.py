"""Validation findings and the report returned by the validator."""

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    message: str
    rule_id: str | None = None
    file: str | None = None

    def format(self) -> str:
        where = self.file or "-"
        subject = f" [{self.rule_id}]" if self.rule_id else ""
        return f"{self.severity.value:7} {self.code}{subject} {where}: {self.message}"


def error(
    code: str, message: str, *, rule_id: str | None = None, file: str | None = None
) -> Finding:
    return Finding(code, Severity.ERROR, message, rule_id, file)


def warning(
    code: str, message: str, *, rule_id: str | None = None, file: str | None = None
) -> Finding:
    return Finding(code, Severity.WARNING, message, rule_id, file)


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    rules_checked: int = 0
    sources_checked: int = 0

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def codes(self) -> set[str]:
        return {f.code for f in self.findings}

    def error_codes(self) -> set[str]:
        return {f.code for f in self.errors}
