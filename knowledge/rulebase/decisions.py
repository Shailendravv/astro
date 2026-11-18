"""Read decision statuses from docs/decisions.md so convention rules cannot outrun the decision log.

A heading looks like `## D-003 Ayanamsha policy ... — PROPOSED (rev. 2)`. A decision counts as accepted only
when its status text says ACCEPTED and mentions neither PROPOSED nor OPEN (so a mixed heading such as
`ACCEPTED (principle) / PROPOSED (values)` is not treated as fully accepted).
"""

import re
from dataclasses import dataclass
from pathlib import Path

_HEADING = re.compile(r"^##\s+(D-\d{3})\b.*?\s—\s(.+?)\s*$", re.MULTILINE)
_WORDS = re.compile(r"[A-Z]{3,}")


@dataclass(frozen=True)
class DecisionInfo:
    decision_id: str
    status_text: str
    accepted: bool


def parse_decisions(text: str) -> dict[str, DecisionInfo]:
    decisions: dict[str, DecisionInfo] = {}
    for match in _HEADING.finditer(text):
        decision_id, status_text = match.group(1), match.group(2)
        words = set(_WORDS.findall(status_text))
        accepted = "ACCEPTED" in words and not ({"PROPOSED", "OPEN"} & words)
        decisions[decision_id] = DecisionInfo(decision_id, status_text, accepted)
    return decisions


def load_decisions(path: Path) -> dict[str, DecisionInfo] | None:
    """None when the decision log does not exist."""
    if not path.is_file():
        return None
    return parse_decisions(path.read_text(encoding="utf-8"))
