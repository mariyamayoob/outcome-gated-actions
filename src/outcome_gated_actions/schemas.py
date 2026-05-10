"""Schema definitions for the experiment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_ACTIONS = (
    "APPROVE",
    "DENY",
    "ASK_CLARIFYING_QUESTION",
    "ESCALATE",
    "NO_ACTION",
)


def _require_non_empty_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _require_string_list(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(value)


def validate_action(action: str) -> str:
    if action not in ALLOWED_ACTIONS:
        allowed = ", ".join(ALLOWED_ACTIONS)
        raise ValueError(f"decision must be one of: {allowed}")
    return action


@dataclass(frozen=True)
class SupportCase:
    id: str
    category: str
    case_text: str
    policy_text: str
    expected_action: str
    must_satisfy: tuple[str, ...]
    must_not_do: tuple[str, ...]
    rubric: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SupportCase":
        rubric = data.get("rubric")
        if not isinstance(rubric, dict):
            raise ValueError("rubric must be an object")

        constraints = rubric.get("constraints")
        if not isinstance(constraints, list):
            raise ValueError("rubric.constraints must be a list")
        for constraint in constraints:
            if not isinstance(constraint, dict):
                raise ValueError("each rubric constraint must be an object")
            validate_action(_require_non_empty_string(constraint, "action"))
            _require_string_list(constraint, "criteria")

        expected_action = validate_action(_require_non_empty_string(data, "expected_action"))

        return cls(
            id=_require_non_empty_string(data, "id"),
            category=_require_non_empty_string(data, "category"),
            case_text=_require_non_empty_string(data, "case_text"),
            policy_text=_require_non_empty_string(data, "policy_text"),
            expected_action=expected_action,
            must_satisfy=_require_string_list(data, "must_satisfy"),
            must_not_do=_require_string_list(data, "must_not_do"),
            rubric=rubric,
        )

    @property
    def constraints(self) -> tuple[dict[str, Any], ...]:
        return tuple(self.rubric["constraints"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "case_text": self.case_text,
            "policy_text": self.policy_text,
            "expected_action": self.expected_action,
            "must_satisfy": list(self.must_satisfy),
            "must_not_do": list(self.must_not_do),
            "rubric": self.rubric,
        }


@dataclass(frozen=True)
class AgentDecision:
    decision: str
    reason: str
    next_action: str
    risk_flags: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDecision":
        risk_flags = data.get("risk_flags", [])
        if not isinstance(risk_flags, list) or not all(isinstance(flag, str) for flag in risk_flags):
            raise ValueError("risk_flags must be a list of strings")
        return cls(
            decision=validate_action(_require_non_empty_string(data, "decision")),
            reason=_require_non_empty_string(data, "reason"),
            next_action=_require_non_empty_string(data, "next_action"),
            risk_flags=tuple(risk_flags),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "next_action": self.next_action,
            "risk_flags": list(self.risk_flags),
        }


@dataclass(frozen=True)
class JudgeResult:
    passed: bool
    failed_criteria: tuple[str, ...]
    explanation: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JudgeResult":
        passed = data.get("passed")
        if not isinstance(passed, bool):
            raise ValueError("passed must be a boolean")
        failed_criteria = data.get("failed_criteria", [])
        if not isinstance(failed_criteria, list) or not all(
            isinstance(item, str) for item in failed_criteria
        ):
            raise ValueError("failed_criteria must be a list of strings")
        return cls(
            passed=passed,
            failed_criteria=tuple(failed_criteria),
            explanation=_require_non_empty_string(data, "explanation"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failed_criteria": list(self.failed_criteria),
            "explanation": self.explanation,
        }


def load_cases(path: Path | str) -> list[SupportCase]:
    rows = read_jsonl(path)
    return [SupportCase.from_dict(row) for row in rows]


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number} of {path}") from exc
    return records


def write_jsonl(path: Path | str, records: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
