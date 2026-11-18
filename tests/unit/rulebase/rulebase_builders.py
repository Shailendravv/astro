"""Builders for synthetic rulebases used by the validator tests.

Everything here is SYNTHETIC: the statements are placeholders that test the validator, not Jyotish claims,
and the sources and decisions exist only inside temporary directories.
"""

import copy
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from knowledge.rulebase.enums import NAMESPACE_DIR, Namespace
from knowledge.rulebase.hashing import version_hash
from knowledge.rulebase.loader import RulebasePaths
from knowledge.rulebase.yamlio import dump_yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TODAY = date(2026, 11, 18)
CREATED = date(2026, 11, 10)

PREFIX_NAMESPACE = {"PAR": "PARASHARI", "KP": "KP", "JAI": "JAIMINI", "SHR": "SHARED"}
CODE_TOPIC = {
    "ASP": "aspect",
    "SUB": "sub_lord",
    "KRK": "karaka",
    "NAK": "nakshatra",
    "AYN": "ayanamsha",
    "NOD": "node",
    "DSH": "dasha",
    "CHD": "chara_dasha",
    "YOG": "yoga",
    "HSE": "house_system",
    "BND": "boundary",
    "VRG": "varga",
}

DECISIONS_TEXT = """# Decisions

## D-901 Synthetic accepted decision — ACCEPTED (test)

## D-902 Synthetic proposed decision — PROPOSED (rev. 1)

## D-903 Synthetic mixed decision — ACCEPTED (principle) / PROPOSED (values)
"""

SYNTHETIC = "SYNTHETIC EXAMPLE for validator tests. Not a Jyotish claim."


def source(source_id: str = "SRC-TEST-A", **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "source_id": source_id,
        "title": "Synthetic test source",
        "edition": "Synthetic edition 1",
        "publisher": "Synthetic Press",
        "year": 2000,
        "language": ["en"],
        "traditions": ["GENERAL"],
        "rights": "OWNED_COPY_PERSONAL_USE",
        "ownership": "OWNER_CONFIRMED",
    }
    data.update(overrides)
    return data


def citation(
    citation_id: str = "SRC-TEST-A:ch1:v1",
    relation: str = "SUPPORTS",
    *,
    reviewed: bool = True,
    **overrides: Any,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "citation_id": citation_id,
        "relation": relation,
        "quote": "Synthetic quote used only in tests.",
        "chapter": "1",
        "page": "10",
        "passage_review_status": "REVIEWED" if reviewed else "UNREVIEWED",
    }
    data.update(overrides)
    return data


def interpretive_content(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "title": "Synthetic interpretive rule",
        "statement": SYNTHETIC,
        "citations": [citation()],
        "conditions": [{"text": "Synthetic condition"}],
        "effect": "Synthetic effect",
    }
    data.update(overrides)
    return data


def calculation_content(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "title": "Synthetic calculation rule",
        "statement": SYNTHETIC,
        "citations": [citation()],
        "formal_spec": "synthetic_output = f(synthetic_input)",
        "inputs": ["synthetic_input"],
        "outputs": ["synthetic_output"],
    }
    data.update(overrides)
    return data


def convention_content(
    setting_key: str = "ayanamsha",
    profiles: tuple[str, ...] = ("parashari-lahiri",),
    decision_ref: str = "D-901",
    chosen_value: str | None = "synthetic-value",
    **overrides: Any,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "title": "Synthetic convention",
        "statement": SYNTHETIC,
        "citations": [citation()],
        "convention": {
            "setting_key": setting_key,
            "applies_to_profiles": list(profiles),
            "chosen_value": chosen_value,
            "alternatives": [{"value": "synthetic-alternative"}],
            "decision_ref": decision_ref,
        },
    }
    data.update(overrides)
    return data


def default_content(rule_type: str) -> dict[str, Any]:
    return {
        "INTERPRETIVE_RULE": interpretive_content,
        "CALCULATION_RULE": calculation_content,
        "CALCULATION_CONVENTION": convention_content,
    }[rule_type]()


def seal(raw: dict[str, Any]) -> dict[str, Any]:
    """Recompute every content_hash and every review's content_hash from the current content."""
    hashes = {}
    for entry in raw["versions"]:
        entry["content_hash"] = version_hash(raw["rule_id"], entry["version"], entry["content"])
        hashes[entry["version"]] = entry["content_hash"]
    for review in raw.get("reviews", []):
        review["content_hash"] = hashes.get(review["rule_version"], review["content_hash"])
    return raw


def _supports(content: dict[str, Any]) -> list[str]:
    return [c["citation_id"] for c in content.get("citations", []) if c["relation"] == "SUPPORTS"]


def _event(
    raw: dict[str, Any],
    version: int,
    previous: str | None,
    target: str,
    day: int,
    *,
    owner: bool = False,
    review_id: str | None = None,
    reason: str | None = None,
) -> None:
    event: dict[str, Any] = {
        "event_id": f"E-{len(raw['lifecycle']) + 1:04d}",
        "rule_version": version,
        "from": previous,
        "to": target,
        "date": date(2026, 11, day),
        "actor": "OWNER" if owner else "CLAUDE_CODE",
    }
    if owner:
        event["recorded_via"] = "CLI_INTERACTIVE"
    if review_id:
        event["review_id"] = review_id
    if reason:
        event["reason"] = reason
    raw["lifecycle"].append(event)


def _owner_review(raw: dict[str, Any], version: int, verdict: str, day: int) -> str:
    entry = next(e for e in raw["versions"] if e["version"] == version)
    review_id = f"R-{len(raw['reviews']) + 1:04d}"
    raw["reviews"].append(
        {
            "review_id": review_id,
            "rule_version": version,
            "content_hash": entry["content_hash"],
            "actor": "OWNER",
            "review_type": "SOURCE_APPROVAL",
            "verdict": verdict,
            "date": date(2026, 11, day),
            "recorded_via": "CLI_INTERACTIVE",
            "evidence": {"citation_ids": _supports(entry["content"])}
            if verdict == "APPROVE"
            else {},
        }
    )
    return review_id


add_event = _event
add_owner_review = _owner_review


def apply_status(raw: dict[str, Any], version: int, status: str) -> None:
    """Append the events (and owner reviews) that bring `version` to `status`, the legal way."""
    if status == "DRAFT":
        _event(raw, version, None, "DRAFT", 11)
        return
    _event(raw, version, None, "PROVISIONAL", 11)
    if status == "PROVISIONAL":
        return
    if status == "VERIFIED":
        rid = _owner_review(raw, version, "APPROVE", 12)
        _event(raw, version, "PROVISIONAL", "VERIFIED", 12, owner=True, review_id=rid)
    elif status == "REJECTED":
        rid = _owner_review(raw, version, "REJECT", 12)
        _event(
            raw,
            version,
            "PROVISIONAL",
            "REJECTED",
            12,
            owner=True,
            review_id=rid,
            reason="Synthetic rejection",
        )
    elif status == "CONFLICTING_SOURCES":
        _event(
            raw,
            version,
            "PROVISIONAL",
            "CONFLICTING_SOURCES",
            12,
            reason="Synthetic conflict between sources",
        )
    else:
        raise ValueError(status)


def make_rule(
    rule_id: str = "PAR-ASP-0001",
    *,
    rule_type: str = "INTERPRETIVE_RULE",
    status: str = "PROVISIONAL",
    content: dict[str, Any] | None = None,
    **top_level: Any,
) -> dict[str, Any]:
    prefix, code, _ = rule_id.split("-")
    raw: dict[str, Any] = {
        "schema_version": 1,
        "rule_id": rule_id,
        "namespace": PREFIX_NAMESPACE[prefix],
        "rule_type": rule_type,
        "topic": CODE_TOPIC[code],
        "terms": ["synthetic_term"],
        "independent_validation": "NONE",
        "versions": [
            {
                "version": 1,
                "created": CREATED,
                "created_by": {"actor": "CLAUDE_CODE"},
                "change_note": "Synthetic initial draft",
                "content": content if content is not None else default_content(rule_type),
            }
        ],
        "reviews": [],
        "lifecycle": [],
    }
    raw.update(top_level)
    seal(raw)
    apply_status(raw, 1, status)
    return raw


def append_version(
    raw: dict[str, Any], status: str = "PROVISIONAL", **content_changes: Any
) -> dict[str, Any]:
    """Add the next version (new content, new hash, fresh lifecycle) the legal way."""
    last = raw["versions"][-1]
    content = copy.deepcopy(last["content"])
    content.update(content_changes)
    if "statement" not in content_changes:
        content["statement"] = last["content"]["statement"] + " (revised)"
    raw["versions"].append(
        {
            "version": last["version"] + 1,
            "created": date(2026, 11, 13),
            "created_by": {"actor": "CLAUDE_CODE"},
            "change_note": "Synthetic revision",
            "content": content,
        }
    )
    seal(raw)
    apply_status_dated(raw, last["version"] + 1, status)
    return raw


def apply_status_dated(raw: dict[str, Any], version: int, status: str) -> None:
    """Like apply_status, but with dates after the version's creation (for later versions)."""
    before = len(raw["lifecycle"]), len(raw["reviews"])
    apply_status(raw, version, status)
    # shift the freshly added items to dates >= the version's creation date
    for event in raw["lifecycle"][before[0] :]:
        event["date"] = date(
            2026, 11, 14 if event["to"] in ("VERIFIED", "REJECTED", "CONFLICTING_SOURCES") else 13
        )
    for review in raw["reviews"][before[1] :]:
        review["date"] = date(2026, 11, 14)


def write_repo(
    tmp_path: Path,
    rules: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
    decisions: str | None = DECISIONS_TEXT,
    *,
    seal_rules: bool = False,
) -> RulebasePaths:
    """Create a synthetic repository layout under tmp_path and return its paths."""
    paths = RulebasePaths.from_root(tmp_path)
    for namespace in Namespace:
        (paths.rules_dir / NAMESPACE_DIR[namespace]).mkdir(parents=True, exist_ok=True)
    paths.catalog_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "knowledge" / "rules" / "_vocabulary.yaml", paths.vocabulary_file)
    if decisions is not None:
        paths.decisions_file.parent.mkdir(parents=True, exist_ok=True)
        paths.decisions_file.write_text(decisions, encoding="utf-8")
    for entry in sources if sources is not None else [source()]:
        (paths.catalog_dir / f"{entry['source_id']}.yaml").write_text(
            dump_yaml(entry), encoding="utf-8"
        )
    for raw in rules or []:
        if seal_rules:
            seal(raw)
        write_rule(paths, raw)
    return paths


def rule_path(paths: RulebasePaths, raw: dict[str, Any]) -> Path:
    namespace = Namespace(raw["namespace"])
    return paths.rules_dir / NAMESPACE_DIR[namespace] / f"{raw['rule_id']}.yaml"


def write_rule(paths: RulebasePaths, raw: dict[str, Any]) -> Path:
    path = rule_path(paths, raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(raw), encoding="utf-8", newline="\n")
    return path
