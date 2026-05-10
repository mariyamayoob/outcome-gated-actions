"""OpenAI support decision provider."""

from __future__ import annotations

import os
from typing import Literal, Protocol

from openai import OpenAI
from pydantic import BaseModel, Field

from outcome_gated_actions.prompts import build_decision_messages
from outcome_gated_actions.schemas import AgentDecision, SupportCase

PROMPT_VERSION = "support_decision_v1"
TEMPERATURE = 0.0


class OpenAIDecisionOutput(BaseModel):
    decision: Literal[
        "APPROVE",
        "DENY",
        "ASK_CLARIFYING_QUESTION",
        "ESCALATE",
        "NO_ACTION",
    ]
    reason: str = Field(description="Short reason for the selected action.")
    next_action: str = Field(description="Short operational next step.")
    risk_flags: list[str] = Field(
        description="Short risk flags. Use an empty list when none apply."
    )


class DecisionProvider(Protocol):
    def decide(
        self,
        case: SupportCase,
        failed_criteria: list[str] | None = None,
    ) -> AgentDecision:
        """Return one closed-set support action."""

    def metadata(self) -> dict[str, str | float]:
        """Return run metadata for outputs."""


class OpenAIProvider:
    """Support decision provider backed by OpenAI."""

    def __init__(self, model: str, client: OpenAI | None = None):
        self.model = model
        self.client = client or OpenAI()

    @classmethod
    def from_env(cls) -> "OpenAIProvider":
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required to run the OpenAI support agent")
        model = os.environ.get("OUTCOME_GATED_MODEL")
        if not model:
            raise ValueError("OUTCOME_GATED_MODEL is required for OpenAI mode")
        return cls(model=model)

    def decide(
        self,
        case: SupportCase,
        failed_criteria: list[str] | None = None,
    ) -> AgentDecision:
        response = self.client.responses.parse(
            model=self.model,
            input=build_decision_messages(case, failed_criteria),
            text_format=OpenAIDecisionOutput,
            temperature=TEMPERATURE,
        )
        parsed = response.output_parsed
        if not parsed:
            raise ValueError("OpenAI response did not contain a structured decision")
        return AgentDecision.from_dict(parsed.model_dump())

    def metadata(self) -> dict[str, str | float]:
        return {
            "provider": "openai",
            "api": "responses",
            "model": self.model,
            "prompt_version": PROMPT_VERSION,
            "temperature": TEMPERATURE,
        }


def get_provider_from_env() -> DecisionProvider:
    provider = os.environ.get("OUTCOME_GATED_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return OpenAIProvider.from_env()
    raise ValueError("OUTCOME_GATED_PROVIDER must be openai")
