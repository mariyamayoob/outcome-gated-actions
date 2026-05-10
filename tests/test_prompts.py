from __future__ import annotations

import json

from outcome_gated_actions.prompts import build_decision_messages, build_judge_payload
from outcome_gated_actions.schemas import AgentDecision, load_cases


def test_agent_prompt_contains_visible_inputs_only() -> None:
    case = next(case for case in load_cases("data/cases.jsonl") if case.id == "auth_01")

    messages = build_decision_messages(case)
    payload = json.loads(messages[1]["content"])

    assert payload["case_text"] == case.case_text
    assert payload["policy_text"] == case.policy_text
    assert payload["closed_action_set"] == [
        "APPROVE",
        "DENY",
        "ASK_CLARIFYING_QUESTION",
        "ESCALATE",
        "NO_ACTION",
    ]
    assert "must_satisfy" not in payload
    assert "must_not_do" not in payload
    assert "expected_action" not in payload
    assert "rubric" not in payload


def test_judge_payload_contains_constraints_not_answer_key() -> None:
    case = next(case for case in load_cases("data/cases.jsonl") if case.id == "auth_01")
    decision = AgentDecision(
        decision="APPROVE",
        reason="The requester knows an account detail.",
        next_action="Change the email.",
        risk_flags=(),
    )

    payload = build_judge_payload(case, decision)

    assert payload["agent_decision"]["decision"] == "APPROVE"
    assert payload["case_text"] == case.case_text
    assert payload["policy_text"] == case.policy_text
    assert payload["rubric_constraints"] == list(case.constraints)
    assert "expected_action" not in payload
