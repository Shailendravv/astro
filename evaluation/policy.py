"""Evaluation policy: judge labelling and owner spot-check sampling (D-022, Q-012, Q-018).

Owner decisions of 2026-11-18, encoded here so the future runner (M3) cannot get them wrong:

- When the judge model is the runtime model (same provider and ID), the run is labelled SELF_JUDGED.
- Spot-check rule (Q-012, PROVISIONALLY accepted; its status stays PROPOSED): review ALL failures; sample 10% of
  passing cases, or 25% when self-judged, rounded up; a minimum of 5 only when at least 5 eligible passing
  cases exist; never more cases than exist.
      sample = min(eligible, max(ceil(rate * eligible), min(5, eligible)))
- A judge verdict is advisory. It can never establish VERIFIED status by itself: only the owner's source
  approval plus independent evidence does (D-022).

No model is called here. The functions are pure.
"""

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

STANDARD_RATE = Fraction(1, 10)
SELF_JUDGED_RATE = Fraction(1, 4)
MINIMUM_SAMPLE = 5
SELECTION_METHOD = "SHA256_RANK_WITH_RECORDED_SEED"


class JudgeMode(StrEnum):
    SELF_JUDGED = "SELF_JUDGED"  # judge provider + model ID equal the runtime's
    INDEPENDENT = "INDEPENDENT"  # a different judge model (still advisory)
    NO_JUDGE = "NO_JUDGE"  # tier 1 automatic checks and owner spot-checks only


def judge_mode(
    runtime_provider: str,
    runtime_model_id: str,
    judge_provider: str | None,
    judge_model_id: str | None,
) -> JudgeMode:
    """Label a run. Equal provider and model ID (ignoring case and spaces) means SELF_JUDGED."""
    if not runtime_provider.strip() or not runtime_model_id.strip():
        raise ValueError("a run needs a configured runtime provider and exact model ID")
    if not (judge_provider or "").strip() or not (judge_model_id or "").strip():
        return JudgeMode.NO_JUDGE
    same = (
        runtime_provider.strip().casefold() == (judge_provider or "").strip().casefold()
        and runtime_model_id.strip().casefold() == (judge_model_id or "").strip().casefold()
    )
    return JudgeMode.SELF_JUDGED if same else JudgeMode.INDEPENDENT


def spot_check_rate(mode: JudgeMode) -> Fraction:
    return SELF_JUDGED_RATE if mode is JudgeMode.SELF_JUDGED else STANDARD_RATE


def judge_verdict_can_establish_verified(mode: JudgeMode) -> bool:
    """Always False. A self-judged verdict is advisory; even an independent judge's is not enough alone."""
    return False


def sample_size(eligible: int, rate: Fraction) -> int:
    """`min(eligible, max(ceil(rate * eligible), min(5, eligible)))` in exact integer arithmetic."""
    if eligible < 0:
        raise ValueError("eligible must not be negative")
    if not 0 < rate <= 1:
        raise ValueError("rate must be in (0, 1]")
    rounded_up = -((-eligible * rate.numerator) // rate.denominator)
    return min(eligible, max(rounded_up, min(MINIMUM_SAMPLE, eligible)))


@dataclass(frozen=True)
class SpotCheckSample:
    """The record stored with a run (data-model.md section 6.3 `spot_check_sample`)."""

    method: str
    seed: int
    suite: str
    language: str
    judge_mode: JudgeMode
    rate: Fraction
    eligible_count: int
    sample_size: int
    selected_case_ids: tuple[str, ...]
    failed_case_ids: tuple[str, ...]

    @property
    def cases_to_review(self) -> tuple[str, ...]:
        """Every failure, then the sampled passes."""
        return self.failed_case_ids + self.selected_case_ids


def select_spot_check(
    suite: str,
    language: str,
    passed_case_ids: list[str],
    failed_case_ids: list[str],
    mode: JudgeMode,
    seed: int,
) -> SpotCheckSample:
    """Applied per suite and language. All failures are reviewed; passes are sampled by a seeded hash rank,
    so the same inputs and seed always give the same selection."""
    overlap = set(passed_case_ids) & set(failed_case_ids)
    if overlap:
        raise ValueError(f"cases both passed and failed: {sorted(overlap)}")
    eligible = sorted(set(passed_case_ids))
    rate = spot_check_rate(mode)
    size = sample_size(len(eligible), rate)
    ranked = sorted(
        eligible, key=lambda case_id: hashlib.sha256(f"{seed}:{case_id}".encode()).hexdigest()
    )
    return SpotCheckSample(
        method=SELECTION_METHOD,
        seed=seed,
        suite=suite,
        language=language,
        judge_mode=mode,
        rate=rate,
        eligible_count=len(eligible),
        sample_size=size,
        selected_case_ids=tuple(sorted(ranked[:size])),
        failed_case_ids=tuple(sorted(set(failed_case_ids))),
    )
