"""Owner decisions and sealing.

`apply_owner_decision` is the only code path that writes an owner SOURCE_APPROVAL review and a VERIFIED or
REJECTED lifecycle event. It refuses unless the caller says the session is interactive and the owner has typed
the exact rule ID. The command-line wrapper (`jyotish rules approve`) refuses when there is no terminal, so
scripts and AI agents cannot approve anything. After writing, the rulebase is validated again; if the result
would not validate, the file is restored byte for byte.

This is a procedural control, not cryptographic proof of identity (D-031, Q-020).
"""

import copy
from datetime import date
from pathlib import Path
from typing import Any, Literal

from knowledge.rulebase.enums import CitationRelation, Status
from knowledge.rulebase.hashing import version_hash
from knowledge.rulebase.lifecycle import latest_version, status_of_version
from knowledge.rulebase.loader import RulebasePaths, load_rulebase
from knowledge.rulebase.validator import validate_loaded
from knowledge.rulebase.yamlio import YamlError, dump_yaml, load_yaml_text


class ApprovalError(RuntimeError):
    """The requested owner action was refused. Nothing was written."""


def seal_file(path: Path) -> list[int]:
    """Write `content_hash` for versions that lack one. Never overwrites an existing hash.

    A wrong existing hash is reported by the validator (VERSION-HASH): fixing it by re-sealing would hide an
    edit to a recorded version, so that is deliberately not offered.
    """
    try:
        raw = load_yaml_text(path.read_text(encoding="utf-8"))
    except YamlError as problem:
        raise ApprovalError(f"{path.name}: {problem}") from problem
    if not isinstance(raw, dict) or not isinstance(raw.get("versions"), list):
        raise ApprovalError(f"{path.name}: not a rule file")
    sealed: list[int] = []
    for entry in raw["versions"]:
        if isinstance(entry, dict) and "content_hash" not in entry:
            entry["content_hash"] = version_hash(
                str(raw.get("rule_id")), int(entry["version"]), entry["content"]
            )
            sealed.append(int(entry["version"]))
    if sealed:
        path.write_text(dump_yaml(raw), encoding="utf-8", newline="\n")
    return sealed


def apply_owner_decision(
    paths: RulebasePaths,
    rule_id: str,
    version: int,
    decision: Literal["APPROVE", "REJECT"],
    *,
    interactive: bool,
    typed_confirmation: str,
    reason: str | None = None,
    notes: str | None = None,
    today: date | None = None,
) -> Path:
    if not interactive:
        raise ApprovalError(
            "owner decisions need an interactive terminal: run `jyotish rules approve` yourself. "
            "Scripts and AI agents cannot approve or reject rules"
        )
    today = today or date.today()
    rulebase = load_rulebase(paths)
    loaded = rulebase.rules.get(rule_id)
    if loaded is None:
        raise ApprovalError(f"rule {rule_id} not found (or its file does not parse)")
    blocking = [f for f in validate_loaded(rulebase, today=today).errors if f.rule_id == rule_id]
    if blocking:
        codes = ", ".join(sorted({f.code for f in blocking}))
        raise ApprovalError(f"{rule_id} has validation errors ({codes}); fix them before deciding")
    model = loaded.model
    if version != latest_version(model):
        raise ApprovalError(
            f"only the latest version ({latest_version(model)}) can be decided, not {version}"
        )
    status = status_of_version(model, version)
    if decision == "APPROVE" and status not in (Status.PROVISIONAL, Status.CONFLICTING_SOURCES):
        raise ApprovalError(
            f"only PROVISIONAL or CONFLICTING_SOURCES versions can be approved, this one is {status}"
        )
    if decision == "REJECT":
        if status is Status.REJECTED:
            raise ApprovalError("this version is already REJECTED")
        if not (reason or "").strip():
            raise ApprovalError("a rejection needs a reason")
    if typed_confirmation != rule_id:
        raise ApprovalError("confirmation did not match the rule ID exactly; nothing was changed")

    entry = next(e for e in model.versions if e.version == version)
    content = loaded.contents[version]
    supports = [c.citation_id for c in content.citations if c.relation is CitationRelation.SUPPORTS]

    raw = copy.deepcopy(loaded.raw)
    review_id = f"R-{len(raw['reviews']) + 1:04d}" if raw.get("reviews") else "R-0001"
    event_id = f"E-{len(raw['lifecycle']) + 1:04d}"
    review: dict[str, Any] = {
        "review_id": review_id,
        "rule_version": version,
        "content_hash": entry.content_hash,
        "actor": "OWNER",
        "review_type": "SOURCE_APPROVAL",
        "verdict": decision,
        "date": today,
        "recorded_via": "CLI_INTERACTIVE",
        "evidence": {"citation_ids": supports} if decision == "APPROVE" else {},
    }
    if notes:
        review["notes"] = notes
    event: dict[str, Any] = {
        "event_id": event_id,
        "rule_version": version,
        "from": status.value if status else None,
        "to": "VERIFIED" if decision == "APPROVE" else "REJECTED",
        "date": today,
        "actor": "OWNER",
        "recorded_via": "CLI_INTERACTIVE",
        "review_id": review_id,
    }
    if reason:
        event["reason"] = reason
    raw.setdefault("reviews", []).append(review)
    raw["lifecycle"].append(event)

    original = loaded.path.read_bytes()
    loaded.path.write_text(dump_yaml(raw), encoding="utf-8", newline="\n")
    after = [
        f for f in validate_loaded(load_rulebase(paths), today=today).errors if f.rule_id == rule_id
    ]
    if after:
        loaded.path.write_bytes(original)
        codes = ", ".join(sorted({f.code for f in after}))
        raise ApprovalError(
            f"the decision would leave {rule_id} invalid ({codes}); file restored, nothing changed"
        )
    return loaded.path
