"""Prompt helpers for optional real provider mode."""

from __future__ import annotations

import json
from typing import Any

from outcome_gated_actions.schemas import ALLOWED_ACTIONS, AgentDecision, SupportCase


def build_decision_messages(
    case: SupportCase,
    failed_criteria: list[str] | None = None,
) -> list[dict[str, str]]:
    retry_note = ""
    if failed_criteria:
        retry_note = (
            "\nThe previous answer failed these objective criteria:\n"
            + "\n".join(f"- {criterion}" for criterion in failed_criteria)
            + "\nChoose a corrected final action."
        )

    user_payload: dict[str, Any] = {
        "case_id": case.id,
        "case_text": case.case_text,
        "policy_text": case.policy_text,
        "closed_action_set": list(ALLOWED_ACTIONS),
        "response_schema": {
            "decision": "APPROVE | DENY | ASK_CLARIFYING_QUESTION | ESCALATE | NO_ACTION",
            "reason": "short reason",
            "next_action": "short action",
            "risk_flags": ["short flags"],
        },
    }

    return [
        {
            "role": "system",
            "content": (
                "You are a support decision agent. Return only valid JSON. "
                "Choose exactly one final action from the closed set."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(user_payload, indent=2) + retry_note,
        },
    ]


def build_judge_payload(case: SupportCase, decision: AgentDecision) -> dict[str, Any]:
    return {
        "agent_decision": decision.to_dict(),
        "case_text": case.case_text,
        "policy_text": case.policy_text,
        "rubric_constraints": list(case.constraints),
    }
