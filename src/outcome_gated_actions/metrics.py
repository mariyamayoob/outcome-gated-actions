"""Metric helpers for experiment outputs."""

from __future__ import annotations

from typing import Any


def calculate_metrics(baseline_records: list[dict[str, Any]], gated_records: list[dict[str, Any]]) -> dict[str, float]:
    if len(baseline_records) != len(gated_records):
        raise ValueError("baseline and gated outputs must contain the same number of records")
    case_count = len(gated_records)
    if case_count == 0:
        raise ValueError("cannot calculate metrics for empty outputs")

    baseline_wrong_actions = sum(_is_wrong(record) for record in baseline_records)
    gated_wrong_actions = sum(_is_wrong(record) for record in gated_records)
    retry_count = sum(bool(record.get("retried")) for record in gated_records)
    fixed_after_retry = sum(bool(record.get("fixed_after_retry")) for record in gated_records)
    false_rejections = sum(bool(record.get("false_rejection")) for record in gated_records)
    total_calls = sum(int(record.get("calls", 0)) for record in gated_records)

    return {
        "baseline_wrong_actions": baseline_wrong_actions,
        "baseline_wrong_action_rate": baseline_wrong_actions / case_count,
        "gated_wrong_actions": gated_wrong_actions,
        "gated_wrong_action_rate": gated_wrong_actions / case_count,
        "fixed_after_retry": fixed_after_retry,
        "false_rejections": false_rejections,
        "retry_rate": retry_count / case_count,
        "average_calls_per_case": total_calls / case_count,
    }


def _is_wrong(record: dict[str, Any]) -> bool:
    if "wrong_action" in record:
        return bool(record["wrong_action"])
    final = record.get("final", {})
    return final.get("decision") != record.get("expected_action")
