from __future__ import annotations

import pytest

from outcome_gated_actions.metrics import calculate_metrics


def test_calculates_article_table_metrics() -> None:
    baseline = [
        {"case_id": "a", "expected_action": "APPROVE", "final": {"decision": "APPROVE"}},
        {"case_id": "b", "expected_action": "DENY", "final": {"decision": "APPROVE"}},
        {"case_id": "c", "expected_action": "ESCALATE", "final": {"decision": "APPROVE"}},
    ]
    gated = [
        {
            "case_id": "a",
            "wrong_action": False,
            "initial_wrong_action": False,
            "retried": False,
            "fixed_after_retry": False,
            "false_rejection": False,
            "calls": 1,
        },
        {
            "case_id": "b",
            "wrong_action": False,
            "initial_wrong_action": True,
            "retried": True,
            "fixed_after_retry": True,
            "false_rejection": False,
            "calls": 2,
        },
        {
            "case_id": "c",
            "wrong_action": True,
            "initial_wrong_action": False,
            "retried": True,
            "fixed_after_retry": False,
            "false_rejection": True,
            "calls": 2,
        },
    ]

    metrics = calculate_metrics(baseline, gated)

    assert metrics["baseline_wrong_actions"] == 2
    assert metrics["baseline_wrong_action_rate"] == pytest.approx(2 / 3)
    assert metrics["gated_wrong_actions"] == 1
    assert metrics["gated_wrong_action_rate"] == pytest.approx(1 / 3)
    assert metrics["fixed_after_retry"] == 1
    assert metrics["false_rejections"] == 1
    assert metrics["false_rejection_rate"] == pytest.approx(1 / 2)
    assert metrics["retry_rate"] == pytest.approx(2 / 3)
    assert metrics["average_calls_per_case"] == pytest.approx(5 / 3)


def test_rejects_mismatched_run_lengths() -> None:
    with pytest.raises(ValueError, match="same number"):
        calculate_metrics([{"case_id": "a"}], [])
