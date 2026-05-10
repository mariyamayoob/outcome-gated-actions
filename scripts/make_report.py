"""Create summary outputs from experiment runs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from outcome_gated_actions.report import (
    DEFAULT_FAILURE_EXAMPLES_PATH,
    DEFAULT_SUMMARY_PATH,
    make_report,
)


def main() -> None:
    try:
        metrics = make_report()
    except ValueError as exc:
        raise SystemExit(f"Report error: {exc}") from exc
    print(f"Wrote summary to {DEFAULT_SUMMARY_PATH}")
    print(f"Wrote examples to {DEFAULT_FAILURE_EXAMPLES_PATH}")
    print(
        "baseline_wrong_action_rate="
        f"{metrics['baseline_wrong_action_rate']:.2%}, "
        "gated_wrong_action_rate="
        f"{metrics['gated_wrong_action_rate']:.2%}"
    )


if __name__ == "__main__":
    main()
