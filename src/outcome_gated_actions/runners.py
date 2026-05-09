"""Baseline and gated experiment runners."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from outcome_gated_actions.agent import DecisionProvider, get_provider_from_env
from outcome_gated_actions.judge import RubricJudge
from outcome_gated_actions.schemas import SupportCase, load_cases, write_jsonl

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_PATH = ROOT / "data" / "cases.jsonl"
DEFAULT_BASELINE_PATH = ROOT / "outputs" / "baseline.jsonl"
DEFAULT_GATED_PATH = ROOT / "outputs" / "gated.jsonl"


def run_baseline(
    cases: Iterable[SupportCase],
    provider: DecisionProvider | None = None,
) -> list[dict]:
    decision_provider = provider or get_provider_from_env()
    records: list[dict] = []
    for case in cases:
        final = decision_provider.decide(case)
        records.append(
            {
                "case_id": case.id,
                "category": case.category,
                "expected_action": case.expected_action,
                "final": final.to_dict(),
                "calls": 1,
                "wrong_action": final.decision != case.expected_action,
            }
        )
    return records


def run_gated(
    cases: Iterable[SupportCase],
    provider: DecisionProvider | None = None,
    judge: RubricJudge | None = None,
) -> list[dict]:
    decision_provider = provider or get_provider_from_env()
    rubric_judge = judge or RubricJudge()
    records: list[dict] = []

    for case in cases:
        initial = decision_provider.decide(case)
        initial_judge = rubric_judge.judge(case, initial)
        final = initial
        final_judge = initial_judge
        calls = 1
        retried = False

        if not initial_judge.passed:
            retried = True
            calls += 1
            final = decision_provider.decide(case, list(initial_judge.failed_criteria))
            final_judge = rubric_judge.judge(case, final)

        initial_wrong = initial.decision != case.expected_action
        final_wrong = final.decision != case.expected_action
        records.append(
            {
                "case_id": case.id,
                "category": case.category,
                "expected_action": case.expected_action,
                "initial": initial.to_dict(),
                "initial_judge": initial_judge.to_dict(),
                "retried": retried,
                "final": final.to_dict(),
                "final_judge": final_judge.to_dict(),
                "calls": calls,
                "initial_wrong_action": initial_wrong,
                "wrong_action": final_wrong,
                "fixed_after_retry": retried and initial_wrong and not final_wrong,
                "false_rejection": not initial_wrong and not initial_judge.passed,
            }
        )
    return records


def run_baseline_file(
    cases_path: Path | str = DEFAULT_CASES_PATH,
    output_path: Path | str = DEFAULT_BASELINE_PATH,
) -> list[dict]:
    records = run_baseline(load_cases(cases_path))
    write_jsonl(output_path, records)
    return records


def run_gated_file(
    cases_path: Path | str = DEFAULT_CASES_PATH,
    output_path: Path | str = DEFAULT_GATED_PATH,
) -> list[dict]:
    records = run_gated(load_cases(cases_path))
    write_jsonl(output_path, records)
    return records
