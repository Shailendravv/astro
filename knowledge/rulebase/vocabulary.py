"""Controlled topic vocabulary: `knowledge/rules/_vocabulary.yaml`.

The three-letter code in a rule ID (`PAR-ASP-0001`) must be the code of the rule's topic, and the topic must be
allowed in the rule's namespace. Adding a topic is an ordinary reviewed edit of that file.
"""

import re
from pathlib import Path

from pydantic import ValidationError

from knowledge.rulebase.enums import Namespace
from knowledge.rulebase.findings import Finding, error
from knowledge.rulebase.models import Base
from knowledge.rulebase.yamlio import YamlError, load_yaml_text

CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


class Topic(Base):
    code: str
    namespaces: list[Namespace]
    description: str = ""


class Vocabulary(Base):
    schema_version: int
    topics: dict[str, Topic]


def load_vocabulary(path: Path) -> tuple[dict[str, Topic], list[Finding]]:
    if not path.is_file():
        return {}, [error("VOCAB-MISSING", "rule vocabulary file not found", file=path.name)]
    try:
        vocabulary = Vocabulary.model_validate(load_yaml_text(path.read_text(encoding="utf-8")))
    except (YamlError, ValidationError, UnicodeDecodeError) as problem:
        return {}, [error("VOCAB-SCHEMA", str(problem).replace("\n", " "), file=path.name)]
    findings: list[Finding] = []
    if vocabulary.schema_version != 1:
        findings.append(
            error(
                "VOCAB-SCHEMA",
                f"unsupported schema_version {vocabulary.schema_version}",
                file=path.name,
            )
        )
    codes: dict[str, str] = {}
    for name, topic in vocabulary.topics.items():
        if not CODE_PATTERN.match(topic.code):
            findings.append(
                error(
                    "VOCAB-CODE",
                    f"topic {name!r}: code {topic.code!r} must be 3 capital letters",
                    file=path.name,
                )
            )
        if topic.code in codes:
            findings.append(
                error(
                    "VOCAB-CODE",
                    f"code {topic.code} used by both {codes[topic.code]!r} and {name!r}",
                    file=path.name,
                )
            )
        codes[topic.code] = name
        if not topic.namespaces:
            findings.append(
                error("VOCAB-NAMESPACES", f"topic {name!r} allows no namespace", file=path.name)
            )
    return vocabulary.topics, findings
