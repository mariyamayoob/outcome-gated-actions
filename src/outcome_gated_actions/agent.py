"""OpenAI support decision agent."""

from __future__ import annotations

import json
import os
from typing import Protocol

from openai import OpenAI

from outcome_gated_actions.prompts import build_decision_messages
from outcome_gated_actions.schemas import AgentDecision, SupportCase


class DecisionProvider(Protocol):
    def decide(
        self,
        case: SupportCase,
        failed_criteria: list[str] | None = None,
    ) -> AgentDecision:
        """Return one closed-set support action."""


class OpenAIProvider:
    """Support decision provider backed by OpenAI."""

    def __init__(self, model: str, client: OpenAI | None = None):
        self.model = model
        self.client = client or OpenAI()

    @classmethod
    def from_env(cls) -> "OpenAIProvider":
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required to run the OpenAI support agent")
        model = os.environ.get("OUTCOME_GATED_MODEL") or os.environ.get("OPENAI_MODEL")
        if not model:
            raise ValueError("OUTCOME_GATED_MODEL or OPENAI_MODEL is required")
        return cls(model=model)

    def decide(
        self,
        case: SupportCase,
        failed_criteria: list[str] | None = None,
    ) -> AgentDecision:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=build_decision_messages(case, failed_criteria),
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI response did not contain JSON content")
        return AgentDecision.from_dict(json.loads(content))


def get_provider_from_env() -> DecisionProvider:
    return OpenAIProvider.from_env()
