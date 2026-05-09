"""Agent providers for support decisions."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol

from outcome_gated_actions.prompts import build_decision_messages
from outcome_gated_actions.schemas import AgentDecision, SupportCase


class DecisionProvider(Protocol):
    def decide(
        self,
        case: SupportCase,
        failed_criteria: list[str] | None = None,
    ) -> AgentDecision:
        """Return one closed-set support action."""


class DeterministicFakeProvider:
    """Small fake provider that creates a repeatable before and after comparison."""

    initial_decision_overrides = {
        "auth_01": "APPROVE",
        "auth_02": "APPROVE",
        "auth_05": "APPROVE",
        "auth_06": "APPROVE",
        "workflow_01": "APPROVE",
        "workflow_02": "APPROVE",
        "workflow_04": "APPROVE",
        "exception_01": "APPROVE",
        "exception_02": "APPROVE",
        "exception_03": "ESCALATE",
        "exception_05": "APPROVE",
        "conflict_01": "APPROVE",
        "conflict_03": "DENY",
        "conflict_05": "APPROVE",
    }

    retry_decision_overrides = {
        "conflict_03": "DENY",
        "conflict_05": "APPROVE",
    }

    def decide(
        self,
        case: SupportCase,
        failed_criteria: list[str] | None = None,
    ) -> AgentDecision:
        if failed_criteria:
            decision = self.retry_decision_overrides.get(case.id, case.expected_action)
            return self._decision_for(case, decision, retried=True)

        decision = self.initial_decision_overrides.get(case.id, case.expected_action)
        return self._decision_for(case, decision, retried=False)

    def _decision_for(self, case: SupportCase, decision: str, retried: bool) -> AgentDecision:
        reason, next_action = _decision_text(decision)
        risk_flags: list[str] = []
        if decision != case.expected_action:
            risk_flags.append("simulated_policy_miss")
        if retried:
            risk_flags.append("retry")
        return AgentDecision(
            decision=decision,
            reason=reason,
            next_action=next_action,
            risk_flags=tuple(risk_flags),
        )


class OpenAICompatibleProvider:
    """Minimal OpenAI-compatible chat completions client using only the stdlib."""

    def __init__(self, api_base: str, api_key: str, model: str, timeout_seconds: int = 45):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider":
        api_base = os.environ.get("OUTCOME_GATED_API_BASE", "https://api.openai.com/v1")
        api_key = os.environ.get("OUTCOME_GATED_API_KEY")
        model = os.environ.get("OUTCOME_GATED_MODEL")
        if not api_key or not model:
            raise ValueError(
                "openai-compatible mode requires OUTCOME_GATED_API_KEY and OUTCOME_GATED_MODEL"
            )
        return cls(api_base=api_base, api_key=api_key, model=model)

    def decide(
        self,
        case: SupportCase,
        failed_criteria: list[str] | None = None,
    ) -> AgentDecision:
        payload = {
            "model": self.model,
            "messages": build_decision_messages(case, failed_criteria),
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            url=f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"provider request failed: {exc}") from exc

        content = body["choices"][0]["message"]["content"]
        return AgentDecision.from_dict(json.loads(content))


def get_provider_from_env() -> DecisionProvider:
    provider = os.environ.get("OUTCOME_GATED_PROVIDER", "fake").strip().lower()
    if provider == "fake":
        return DeterministicFakeProvider()
    if provider == "openai-compatible":
        return OpenAICompatibleProvider.from_env()
    raise ValueError(f"unknown OUTCOME_GATED_PROVIDER: {provider}")


def _decision_text(decision: str) -> tuple[str, str]:
    text = {
        "APPROVE": (
            "The request appears to meet the support policy.",
            "Carry out the requested support action.",
        ),
        "DENY": (
            "The request does not meet the policy constraints.",
            "Tell the customer the request cannot be completed.",
        ),
        "ASK_CLARIFYING_QUESTION": (
            "A required verification or policy fact is missing.",
            "Ask for the missing information before acting.",
        ),
        "ESCALATE": (
            "The case needs a specialist or policy owner review.",
            "Route the ticket to the owning review queue.",
        ),
        "NO_ACTION": (
            "An existing workflow already owns the requested outcome.",
            "Leave the existing workflow in place and avoid duplicate action.",
        ),
    }
    return text[decision]
