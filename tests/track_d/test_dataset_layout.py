"""Track D CI slot (M1, T1.7; D-022, D-028).

There are no datasets, rules, or calculations yet, so this stage checks only the layout that later
milestones fill in: M2 adds schema and source-fidelity checks, M3 the runner and freeze check, M4+
the calculation suites. The stage exists and runs in CI now so it cannot be forgotten later.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COLLECTIONS = (
    "astronomy",
    "shared_charts",
    "parashari",
    "kp",
    "jaimini",
    "interpretation",
    "integration",
    "source_fidelity",
)

pytestmark = pytest.mark.track_d


@pytest.mark.parametrize("collection", COLLECTIONS)
def test_dataset_collection_directory_exists(collection: str) -> None:
    assert (ROOT / "evaluation" / "datasets" / collection).is_dir()


def test_no_unreviewed_case_files_before_the_schema_exists() -> None:
    """Golden cases must be written against the M2 case schema, so none may exist yet."""
    case_files = [
        path
        for collection in COLLECTIONS
        for path in (ROOT / "evaluation" / "datasets" / collection).glob("*.y*ml")
    ]
    assert case_files == [], f"cases found before the M2 schema: {case_files}"
