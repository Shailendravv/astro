"""Discover and parse rule files into an in-memory `Rulebase`."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from knowledge.rulebase.decisions import DecisionInfo, load_decisions
from knowledge.rulebase.enums import NAMESPACE_DIR, Namespace
from knowledge.rulebase.findings import Finding, error
from knowledge.rulebase.models import CONTENT_MODELS, ContentBase, RuleFile
from knowledge.rulebase.sources import Source, load_catalog
from knowledge.rulebase.vocabulary import Topic, load_vocabulary
from knowledge.rulebase.yamlio import YamlError, load_yaml_text


@dataclass(frozen=True)
class RulebasePaths:
    root: Path
    rules_dir: Path
    catalog_dir: Path
    decisions_file: Path
    vocabulary_file: Path

    @staticmethod
    def from_root(root: Path) -> "RulebasePaths":
        return RulebasePaths(
            root=root,
            rules_dir=root / "knowledge" / "rules",
            catalog_dir=root / "knowledge" / "source_catalog",
            decisions_file=root / "docs" / "decisions.md",
            vocabulary_file=root / "knowledge" / "rules" / "_vocabulary.yaml",
        )


@dataclass
class LoadedRule:
    path: Path
    rel: str  # path relative to the rules directory, with forward slashes
    raw: dict[str, Any]
    model: RuleFile
    contents: dict[int, ContentBase] = field(
        default_factory=dict
    )  # only versions whose content parsed

    @property
    def rule_id(self) -> str:
        return self.model.rule_id


@dataclass
class Rulebase:
    paths: RulebasePaths
    rules: dict[str, LoadedRule]
    sources: dict[str, Source]
    decisions: dict[str, DecisionInfo] | None
    vocabulary: dict[str, Topic]
    findings: list[Finding]
    rule_files_seen: int
    source_files_seen: int


def _schema_message(problem: ValidationError) -> str:
    parts = []
    for item in problem.errors():
        location = ".".join(str(p) for p in item["loc"]) or "(root)"
        parts.append(f"{location}: {item['msg']}")
    return "; ".join(parts)


def _discover(paths: RulebasePaths) -> tuple[list[Path], list[Finding]]:
    """Rule files live in knowledge/rules/<namespace-dir>/<RULE_ID>.yaml. Anything else is reported."""
    findings: list[Finding] = []
    files: list[Path] = []
    known_dirs = set(NAMESPACE_DIR.values())
    if not paths.rules_dir.is_dir():
        return files, [error("LOAD-NO-RULES-DIR", f"rules directory not found: {paths.rules_dir}")]
    for entry in sorted(paths.rules_dir.iterdir()):
        if entry.is_dir() and entry.name in known_dirs:
            for path in sorted(entry.iterdir()):
                if path.is_dir():
                    findings.append(
                        error(
                            "LOAD-STRAY-DIR",
                            "nested directories are not allowed",
                            file=f"{entry.name}/{path.name}",
                        )
                    )
                elif path.name.startswith(("_", ".")) or path.suffix not in {".yaml", ".yml"}:
                    continue
                elif path.suffix == ".yml":
                    findings.append(
                        error(
                            "LOAD-EXTENSION",
                            "rule files must use the .yaml extension",
                            file=f"{entry.name}/{path.name}",
                        )
                    )
                else:
                    files.append(path)
        elif entry.is_dir() and not entry.name.startswith((".", "_")):
            if any(p.suffix in {".yaml", ".yml"} for p in entry.rglob("*")):
                findings.append(
                    error(
                        "LOAD-UNKNOWN-NAMESPACE",
                        f"directory {entry.name!r} is not a rule namespace ({sorted(known_dirs)})",
                        file=entry.name,
                    )
                )
        elif (
            entry.is_file() and entry.suffix in {".yaml", ".yml"} and not entry.name.startswith("_")
        ):
            findings.append(
                error(
                    "LOAD-MISPLACED",
                    "rule files must sit in a namespace directory",
                    file=entry.name,
                )
            )
    return files, findings


def load_rulebase(paths: RulebasePaths) -> Rulebase:
    findings: list[Finding] = []
    sources, source_findings, source_files = load_catalog(paths.catalog_dir)
    findings.extend(source_findings)
    vocabulary, vocab_findings = load_vocabulary(paths.vocabulary_file)
    findings.extend(vocab_findings)
    decisions = load_decisions(paths.decisions_file)

    files, discovery_findings = _discover(paths)
    findings.extend(discovery_findings)

    rules: dict[str, LoadedRule] = {}
    for path in files:
        rel = path.relative_to(paths.rules_dir).as_posix()
        try:
            raw = load_yaml_text(path.read_text(encoding="utf-8"))
        except (YamlError, UnicodeDecodeError) as problem:
            findings.append(error("FILE-YAML", str(problem), file=rel))
            continue
        if not isinstance(raw, dict):
            findings.append(error("FILE-YAML", "top level must be a mapping", file=rel))
            continue
        try:
            model = RuleFile.model_validate(raw)
        except ValidationError as problem:
            findings.append(
                error(
                    "SCHEMA",
                    _schema_message(problem),
                    rule_id=str(raw.get("rule_id", "?")),
                    file=rel,
                )
            )
            continue
        loaded = LoadedRule(path=path, rel=rel, raw=raw, model=model)
        content_model = CONTENT_MODELS[model.rule_type]
        for entry in model.versions:
            try:
                loaded.contents[entry.version] = content_model.model_validate(entry.content)
            except ValidationError as problem:
                findings.append(
                    error(
                        "CONTENT-SCHEMA",
                        f"version {entry.version} ({model.rule_type.value}): {_schema_message(problem)}",
                        rule_id=model.rule_id,
                        file=rel,
                    )
                )
        if model.rule_id in rules:
            findings.append(
                error(
                    "RULE-DUPLICATE",
                    f"rule_id also defined in {rules[model.rule_id].rel}",
                    rule_id=model.rule_id,
                    file=rel,
                )
            )
            continue
        rules[model.rule_id] = loaded

    return Rulebase(
        paths=paths,
        rules=rules,
        sources=sources,
        decisions=decisions,
        vocabulary=vocabulary,
        findings=findings,
        rule_files_seen=len(files),
        source_files_seen=source_files,
    )


def namespace_of_dir(dir_name: str) -> Namespace | None:
    for namespace, directory in NAMESPACE_DIR.items():
        if directory == dir_name:
            return namespace
    return None
