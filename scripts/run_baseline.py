"""Run the baseline support decision experiment."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from outcome_gated_actions.runners import DEFAULT_BASELINE_PATH, run_baseline_file


def main() -> None:
    records = run_baseline_file()
    print(f"Wrote {len(records)} baseline records to {DEFAULT_BASELINE_PATH}")


if __name__ == "__main__":
    main()
