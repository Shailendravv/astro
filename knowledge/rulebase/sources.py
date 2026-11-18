"""Source catalogue records: `knowledge/source_catalog/<SOURCE_ID>.yaml` (data-model.md section 4.1).

M2 builds the schema only. The real catalogue stays empty until the owner supplies the book inventory
(Q-014): nothing here assumes the owner owns any book.
"""

import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Literal

from pydantic import Field, ValidationError

from knowledge.rulebase.enums import Ownership, Rights
from knowledge.rulebase.findings import Finding, error
from knowledge.rulebase.models import Base
from knowledge.rulebase.yamlio import YamlError, load_yaml_text

SOURCE_ID_PATTERN = re.compile(r"^SRC-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class Source(Base):
    schema_version: int
    source_id: str
    title: str
    author: str | None = None
    translator: str | None = None
    commentator: str | None = None
    edition: str | None = None
    publisher: str | None = None
    year: int | None = None
    language: list[Literal["sa", "hi", "en"]] = Field(default_factory=list)
    traditions: list[Literal["PARASHARI", "KP", "JAIMINI", "GENERAL"]] = Field(default_factory=list)
    rights: Rights
    rights_notes: str | None = None
    ownership: Ownership = Ownership.UNCONFIRMED
    extraction_method: Literal["EMBEDDED_TEXT", "OCR", "MANUAL"] | None = None
    sha256: str | None = None
    file_path: str | None = None  # absolute path under the library root, outside git


def _is_absolute(path: str) -> bool:
    return (
        PurePosixPath(path).is_absolute()
        or PureWindowsPath(path).is_absolute()
        or path.startswith("library:")
    )


def check_source(source: Source, file_name: str) -> list[Finding]:
    findings: list[Finding] = []
    where = file_name
    if not SOURCE_ID_PATTERN.match(source.source_id):
        findings.append(
            error("SRC-ID", f"source_id {source.source_id!r} must match SRC-[A-Z0-9-]+", file=where)
        )
    if file_name != f"{source.source_id}.yaml":
        findings.append(
            error("SRC-FILENAME", f"file name must be {source.source_id}.yaml", file=where)
        )
    if source.schema_version != 1:
        findings.append(
            error(
                "SRC-SCHEMA-VERSION",
                f"unsupported schema_version {source.schema_version}",
                file=where,
            )
        )
    if source.sha256 is not None and not SHA256_PATTERN.match(source.sha256):
        findings.append(
            error("SRC-SHA256", "sha256 must be 64 lowercase hex characters", file=where)
        )
    if source.ownership is Ownership.UNCONFIRMED and (source.sha256 or source.file_path):
        findings.append(
            error(
                "SRC-UNCONFIRMED-INGESTED",
                "an UNCONFIRMED source cannot have a checksum or file path: ingest only after the owner "
                "confirms ownership (Q-014)",
                file=where,
            )
        )
    if source.file_path is not None and not _is_absolute(source.file_path):
        findings.append(
            error(
                "SRC-FILE-PATH",
                "file_path must be absolute (or 'library:' prefixed): library files live outside the repository",
                file=where,
            )
        )
    return findings


def load_catalog(catalog_dir: Path) -> tuple[dict[str, Source], list[Finding], int]:
    """Load every `*.yaml` source record. Returns (sources by id, findings, files seen)."""
    sources: dict[str, Source] = {}
    findings: list[Finding] = []
    seen = 0
    if not catalog_dir.is_dir():
        return sources, findings, seen
    for path in sorted(catalog_dir.iterdir()):
        if not path.is_file() or path.name.startswith("_") or path.suffix != ".yaml":
            continue
        seen += 1
        try:
            raw = load_yaml_text(path.read_text(encoding="utf-8"))
            source = Source.model_validate(raw)
        except (YamlError, ValidationError, UnicodeDecodeError) as problem:
            findings.append(error("SRC-SCHEMA", str(problem).replace("\n", " "), file=path.name))
            continue
        findings.extend(check_source(source, path.name))
        if source.source_id in sources:
            findings.append(
                error("SRC-DUPLICATE", f"duplicate source_id {source.source_id}", file=path.name)
            )
        else:
            sources[source.source_id] = source
    return sources, findings, seen


def source_id_of(citation_id: str) -> str:
    """`SRC-X:ch1:v2` -> `SRC-X`."""
    return citation_id.split(":", 1)[0]
