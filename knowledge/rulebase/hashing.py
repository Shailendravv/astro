"""Content hashes that bind reviews and approvals to the exact text of one rule version."""

import hashlib
import json
from datetime import date
from typing import Any


def _default(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"cannot hash value of type {type(value).__name__}")


def canonical_json(data: Any) -> str:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_default
    )


def version_hash(rule_id: str, version: int, content: dict[str, Any]) -> str:
    """sha256 over the canonical form of (rule_id, version, content). Any content change changes it."""
    payload = canonical_json({"rule_id": rule_id, "version": version, "content": content})
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
