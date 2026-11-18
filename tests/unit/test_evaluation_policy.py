"""Evaluation policy: SELF_JUDGED labelling and the Q-012 spot-check rule (provisionally accepted)."""

import math
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from evaluation.policy import (
    SELF_JUDGED_RATE,
    STANDARD_RATE,
    JudgeMode,
    judge_mode,
    judge_verdict_can_establish_verified,
    sample_size,
    select_spot_check,
    spot_check_rate,
)

# ---------------------------------------------------------------- SELF_JUDGED label


def test_same_provider_and_model_is_self_judged():
    assert judge_mode("groq", "model-x", "groq", "model-x") is JudgeMode.SELF_JUDGED


def test_comparison_ignores_case_and_surrounding_space():
    assert judge_mode("Groq", "Model-X", " groq ", "model-x ") is JudgeMode.SELF_JUDGED


def test_different_model_is_independent_but_still_advisory():
    mode = judge_mode("groq", "model-x", "groq", "model-y")
    assert mode is JudgeMode.INDEPENDENT
    assert judge_verdict_can_establish_verified(mode) is False


def test_same_model_id_on_a_different_provider_is_not_self_judged():
    assert judge_mode("groq", "model-x", "other", "model-x") is JudgeMode.INDEPENDENT


@pytest.mark.parametrize(
    ("provider", "model"), [(None, None), ("groq", None), ("", "x"), (None, "x")]
)
def test_missing_judge_configuration_means_no_judge(provider, model):
    assert judge_mode("groq", "model-x", provider, model) is JudgeMode.NO_JUDGE


@pytest.mark.parametrize(("provider", "model"), [("", "x"), ("groq", " "), ("", "")])
def test_a_run_needs_a_runtime_model(provider, model):
    with pytest.raises(ValueError, match="runtime provider"):
        judge_mode(provider, model, "groq", "x")


@pytest.mark.parametrize("mode", list(JudgeMode))
def test_no_judge_verdict_can_establish_verified(mode):
    """Owner decision 2026-11-18 and D-022: judge results are advisory; only the owner verifies."""
    assert judge_verdict_can_establish_verified(mode) is False


def test_rates_are_25_percent_when_self_judged_otherwise_10():
    assert spot_check_rate(JudgeMode.SELF_JUDGED) == Fraction(1, 4) == SELF_JUDGED_RATE
    assert spot_check_rate(JudgeMode.INDEPENDENT) == Fraction(1, 10) == STANDARD_RATE
    assert spot_check_rate(JudgeMode.NO_JUDGE) == STANDARD_RATE


# ---------------------------------------------------------------- sample size


@pytest.mark.parametrize(
    ("eligible", "rate", "expected"),
    [
        (0, Fraction(1, 4), 0),  # nothing to sample
        (1, Fraction(1, 4), 1),  # fewer than 5: review all of them
        (4, Fraction(1, 10), 4),
        (5, Fraction(1, 10), 5),  # minimum of 5 applies when >= 5 exist
        (12, Fraction(1, 10), 5),  # ceil(1.2) = 2, raised to the minimum 5
        (40, Fraction(1, 10), 5),  # ceil(4) = 4, raised to 5
        (41, Fraction(1, 10), 5),  # ceil(4.1) = 5
        (100, Fraction(1, 10), 10),
        (101, Fraction(1, 10), 11),  # rounded up
        (20, Fraction(1, 4), 5),
        (21, Fraction(1, 4), 6),  # ceil(5.25)
        (100, Fraction(1, 4), 25),
        (3, Fraction(1, 4), 3),
    ],
)
def test_sample_size_examples(eligible, rate, expected):
    assert sample_size(eligible, rate) == expected


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError, match="negative"):
        sample_size(-1, Fraction(1, 4))
    with pytest.raises(ValueError, match="rate"):
        sample_size(10, Fraction(0))
    with pytest.raises(ValueError, match="rate"):
        sample_size(10, Fraction(2))


@given(
    eligible=st.integers(min_value=0, max_value=5000),
    rate=st.sampled_from([STANDARD_RATE, SELF_JUDGED_RATE]),
)
def test_sample_size_properties(eligible, rate):
    size = sample_size(eligible, rate)
    assert 0 <= size <= eligible  # never more than exist
    assert size >= min(5, eligible)  # minimum 5 only when >= 5 exist; otherwise all of them
    assert size >= min(eligible, math.ceil(rate * eligible))  # at least the rounded-up share
    if eligible >= 5:
        assert size >= 5
    if eligible < 5:
        assert size == eligible


@given(eligible=st.integers(min_value=0, max_value=5000))
def test_self_judged_sample_is_never_smaller_than_the_standard_sample(eligible):
    assert sample_size(eligible, SELF_JUDGED_RATE) >= sample_size(eligible, STANDARD_RATE)


@given(eligible=st.integers(min_value=0, max_value=4999))
def test_sample_size_is_monotonic_in_eligible_count(eligible):
    for rate in (STANDARD_RATE, SELF_JUDGED_RATE):
        assert sample_size(eligible + 1, rate) >= sample_size(eligible, rate)


# ---------------------------------------------------------------- selection


def ids(n, prefix="GC-KP-"):
    return [f"{prefix}{i:04d}" for i in range(1, n + 1)]


def test_every_failure_is_reviewed_and_passes_are_sampled():
    sample = select_spot_check(
        "kp", "en", ids(40), ["GC-KP-9001", "GC-KP-9002"], JudgeMode.SELF_JUDGED, seed=7
    )
    assert sample.failed_case_ids == ("GC-KP-9001", "GC-KP-9002")
    assert sample.eligible_count == 40
    assert sample.sample_size == 10  # 25% of 40
    assert len(sample.selected_case_ids) == 10
    assert set(sample.selected_case_ids) <= set(ids(40))
    assert sample.cases_to_review[:2] == ("GC-KP-9001", "GC-KP-9002")
    assert len(sample.cases_to_review) == 12
    assert sample.judge_mode is JudgeMode.SELF_JUDGED
    assert sample.rate == Fraction(1, 4)


def test_selection_is_reproducible_from_the_recorded_seed_and_differs_with_another_seed():
    first = select_spot_check("kp", "en", ids(60), [], JudgeMode.SELF_JUDGED, seed=1)
    again = select_spot_check(
        "kp", "en", list(reversed(ids(60))), [], JudgeMode.SELF_JUDGED, seed=1
    )
    other = select_spot_check("kp", "en", ids(60), [], JudgeMode.SELF_JUDGED, seed=2)
    assert first.selected_case_ids == again.selected_case_ids
    assert first.selected_case_ids != other.selected_case_ids
    assert first.method == "SHA256_RANK_WITH_RECORDED_SEED"
    assert first.seed == 1


def test_fewer_than_five_passes_are_all_reviewed():
    sample = select_spot_check("kp", "hi", ids(3), [], JudgeMode.INDEPENDENT, seed=0)
    assert sample.selected_case_ids == tuple(ids(3))


def test_no_passes_means_an_empty_sample_and_failures_still_reviewed():
    sample = select_spot_check("kp", "en", [], ["GC-KP-0001"], JudgeMode.SELF_JUDGED, seed=0)
    assert sample.selected_case_ids == ()
    assert sample.cases_to_review == ("GC-KP-0001",)


def test_a_case_cannot_be_both_passed_and_failed():
    with pytest.raises(ValueError, match="both passed and failed"):
        select_spot_check("kp", "en", ["A"], ["A"], JudgeMode.SELF_JUDGED, seed=0)


def test_duplicate_ids_do_not_inflate_the_eligible_count():
    sample = select_spot_check("kp", "en", ["A", "A", "B"], [], JudgeMode.INDEPENDENT, seed=0)
    assert sample.eligible_count == 2


@given(
    passed=st.lists(
        st.text(alphabet="ABCDEFGH0123456789", min_size=1, max_size=6), max_size=60, unique=True
    ),
    seed=st.integers(min_value=0, max_value=10**6),
    mode=st.sampled_from(list(JudgeMode)),
)
def test_selection_properties(passed, seed, mode):
    sample = select_spot_check("s", "en", passed, [], mode, seed)
    assert len(sample.selected_case_ids) == sample.sample_size <= sample.eligible_count
    assert set(sample.selected_case_ids) <= set(passed)
    assert len(set(sample.selected_case_ids)) == len(sample.selected_case_ids)
