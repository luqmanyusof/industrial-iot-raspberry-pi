#!/usr/bin/env python3
"""Read the PS-01 data log and print a short shift report."""
import json
from pathlib import Path

DATA_FILE = Path.home() / "iiot" / "data" / "ps01.jsonl"


def main() -> None:
    levels = []
    faults = 0
    bad_lines = 0

    with DATA_FILE.open() as f:
        for line_no, line in enumerate(f, start=1):
            try:
                reading = json.loads(line)
            except json.JSONDecodeError:
                bad_lines += 1
                print(f"Skipping damaged line {line_no}: {line.strip()[:40]}")
                continue

            levels.append(reading["tank_level_pct"])
            if reading["status"] != "OK":
                faults += 1

    if not levels:
        print("No readings yet.")
        return

    print(f"Readings      : {len(levels)}")
    print(f"Tank level    : min {min(levels):.1f}%  max {max(levels):.1f}%  "
          f"avg {sum(levels) / len(levels):.1f}%")
    print(f"Sensor faults : {faults}")
    print(f"Damaged lines : {bad_lines}")


if __name__ == "__main__":
    main()
