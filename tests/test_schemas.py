from __future__ import annotations

import pytest

from outcome_gated_actions.schemas import AgentDecision, SupportCase, load_cases


def test_loads_all_synthetic_cases() -> None:
    cases = load_cases("data/cases.jsonl")

    assert len(cases) == 30
    assert {case.category for case in cases} == {
        "Authentication constraint",
        "Existing workflow constraint",
        "Policy exception",
        "Conflicting evidence",
        "Safe approval",
    }


def test_case_validation_rejects_unknown_action() -> None:
    data = {
        "id": "bad_case",
        "category": "Synthetic",
        "case_text": "A requester asks for support.",
        "policy_text": "Use only known actions.",
        "expected_action": "TRANSFER",
        "must_satisfy": [],
        "must_not_do": [],
        "rubric": {"allowed_actions": ["TRANSFER"], "failures": {}},
    }

    with pytest.raises(ValueError, match="decision must be one of"):
        SupportCase.from_dict(data)


def test_agent_decision_schema_round_trip() -> None:
    decision = AgentDecision.from_dict(
        {
            "decision": "ESCALATE",
            "reason": "Conflicting evidence needs review.",
            "next_action": "Route to the review queue.",
            "risk_flags": ["conflicting_evidence"],
        }
    )

    assert decision.to_dict() == {
        "decision": "ESCALATE",
        "reason": "Conflicting evidence needs review.",
        "next_action": "Route to the review queue.",
        "risk_flags": ["conflicting_evidence"],
    }
