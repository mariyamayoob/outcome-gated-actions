"""Rubric judge for closed-set support actions."""

from __future__ import annotations

from outcome_gated_actions.prompts import build_judge_payload
from outcome_gated_actions.schemas import AgentDecision, JudgeResult, SupportCase


class RubricJudge:
    """Judge only the objective final action, not prose quality."""

    def judge(self, case: SupportCase, decision: AgentDecision) -> JudgeResult:
        judge_payload = build_judge_payload(case, decision)
        selected_action = judge_payload["agent_decision"]["decision"]
        failed_criteria = tuple(
            self._failed_criteria(judge_payload["rubric_constraints"], selected_action)
        )
        if failed_criteria:
            return JudgeResult(
                passed=False,
                failed_criteria=failed_criteria,
                explanation=(
                    f"{decision.decision} violates an objective rubric constraint for {case.id}."
                ),
            )

        return JudgeResult(
            passed=True,
            failed_criteria=(),
            explanation=(
                f"{decision.decision} does not violate the explicit rubric constraints."
            ),
        )

    def _failed_criteria(self, constraints: list[dict], decision: str) -> list[str]:
        failed: list[str] = []
        for constraint in constraints:
            if constraint["action"] == decision:
                failed.extend(constraint["criteria"])
        return failed
