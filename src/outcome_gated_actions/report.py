"""Report generation helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from outcome_gated_actions.metrics import calculate_metrics
from outcome_gated_actions.schemas import read_jsonl

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE_PATH = ROOT / "outputs" / "baseline.jsonl"
DEFAULT_GATED_PATH = ROOT / "outputs" / "gated.jsonl"
DEFAULT_SUMMARY_PATH = ROOT / "outputs" / "summary.csv"
DEFAULT_FAILURE_EXAMPLES_PATH = ROOT / "outputs" / "failure_examples.md"


def make_report(
    baseline_path: Path | str = DEFAULT_BASELINE_PATH,
    gated_path: Path | str = DEFAULT_GATED_PATH,
    summary_path: Path | str = DEFAULT_SUMMARY_PATH,
    failure_examples_path: Path | str = DEFAULT_FAILURE_EXAMPLES_PATH,
) -> dict[str, float]:
    _require_output_file(baseline_path, "baseline")
    _require_output_file(gated_path, "gated")
    baseline_records = read_jsonl(baseline_path)
    gated_records = read_jsonl(gated_path)
    _validate_openai_outputs(baseline_records, gated_records)
    metrics = calculate_metrics(baseline_records, gated_records)
    write_summary_csv(metrics, summary_path)
    write_failure_examples(baseline_records, gated_records, failure_examples_path)
    return metrics


def write_summary_csv(metrics: dict[str, float], path: Path | str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for metric, value in metrics.items():
            writer.writerow([metric, _format_value(value)])


def write_failure_examples(
    baseline_records: list[dict[str, Any]],
    gated_records: list[dict[str, Any]],
    path: Path | str,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    remaining_wrong = [record for record in gated_records if record.get("wrong_action")]
    fixed = [record for record in gated_records if record.get("fixed_after_retry")]

    lines = [
        "# Failure Examples",
        "",
        "These examples are synthetic and are intended for article discussion.",
        "",
        "## Remaining Wrong Final Actions",
        "",
    ]
    if remaining_wrong:
        for record in remaining_wrong:
            lines.extend(_example_lines(record))
    else:
        lines.append("No remaining wrong final actions.")

    lines.extend(["", "## Fixed After Retry", ""])
    if fixed:
        for record in fixed[:8]:
            lines.extend(_example_lines(record))
    else:
        lines.append("No cases were fixed after retry.")

    baseline_wrong = sum(bool(record.get("wrong_action")) for record in baseline_records)
    lines.extend(
        [
            "",
            "## Baseline Context",
            "",
            f"The baseline run produced {baseline_wrong} wrong final actions before gating.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _example_lines(record: dict[str, Any]) -> list[str]:
    initial = record.get("initial", {})
    final = record.get("final", {})
    initial_judge = record.get("initial_judge", {})
    return [
        f"### {record['case_id']}",
        "",
        f"- Category: {record['category']}",
        f"- Case: {record.get('case_text', 'not recorded')}",
        f"- Policy: {record.get('policy_text', 'not recorded')}",
        f"- Expected action: {record['expected_action']}",
        f"- Initial action: {initial.get('decision', 'n/a')}",
        f"- Final action: {final.get('decision', 'n/a')}",
        f"- Retry used: {record.get('retried', False)}",
        f"- Failed criteria: {', '.join(initial_judge.get('failed_criteria', [])) or 'none'}",
        "",
    ]


def _format_value(value: float) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _require_output_file(path: Path | str, run_name: str) -> None:
    if not Path(path).exists():
        raise ValueError(
            f"{run_name} output is missing. Run scripts/run_{run_name}.py before making a report."
        )


def _validate_openai_outputs(
    baseline_records: list[dict[str, Any]],
    gated_records: list[dict[str, Any]],
) -> None:
    for run_name, records in (("baseline", baseline_records), ("gated", gated_records)):
        if not records:
            raise ValueError(f"{run_name} output is empty")
        for record in records:
            metadata = record.get("metadata")
            if not isinstance(metadata, dict) or metadata.get("provider") != "openai":
                raise ValueError(
                    f"{run_name} output is missing OpenAI run metadata. "
                    "Rerun baseline and gated scripts with OPENAI_API_KEY and OUTCOME_GATED_MODEL."
                )
