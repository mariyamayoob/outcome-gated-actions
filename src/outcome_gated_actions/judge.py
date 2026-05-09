"""Rubric judge for closed-set support actions."""

from __future__ import annotations

from outcome_gated_actions.schemas import AgentDecision, JudgeResult, SupportCase


class RubricJudge:
    """Judge only the objective final action, not prose quality."""

    def judge(self, case: SupportCase, decision: AgentDecision) -> JudgeResult:
        if decision.decision in case.allowed_actions:
            return JudgeResult(
                passed=True,
                failed_criteria=(),
                explanation=f"{decision.decision} is allowed by the objective case rubric.",
            )

        failed_criteria = self._failed_criteria(case, decision.decision)
        return JudgeResult(
            passed=False,
            failed_criteria=tuple(failed_criteria),
            explanation=(
                f"{decision.decision} violates the objective action rubric for {case.id}."
            ),
        )

    def _failed_criteria(self, case: SupportCase, decision: str) -> list[str]:
        failures = case.rubric.get("failures", {})
        if isinstance(failures, dict):
            criteria = failures.get(decision, [])
            if isinstance(criteria, list) and all(isinstance(item, str) for item in criteria):
                return criteria

        allowed = ", ".join(case.allowed_actions)
        return [f"{decision} is not allowed for this case. Allowed action: {allowed}."]
