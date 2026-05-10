"""Run the outcome-gated support decision experiment."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from outcome_gated_actions.runners import DEFAULT_GATED_PATH, run_gated_file


def main() -> None:
    try:
        records = run_gated_file()
    except ValueError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc
    print(f"Wrote {len(records)} gated records to {DEFAULT_GATED_PATH}")


if __name__ == "__main__":
    main()
