#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from pegasus_movement.analyzer import analyze_run, write_report


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Calculate M_req and M_obs from one Pegasus runXXXX directory."
    )
    ap.add_argument("--run", required=True, help="Pegasus runXXXX directory")
    ap.add_argument("--history-file", help="Optional `condor_history -long` snapshot")
    ap.add_argument("--placement-tsv", help="Optional TSV with task/worker columns; takes precedence")
    ap.add_argument("--out", default="results/movement_v05", help="Output directory")
    args = ap.parse_args()

    result = analyze_run(
        Path(args.run),
        history_file=Path(args.history_file) if args.history_file else None,
        placement_tsv=Path(args.placement_tsv) if args.placement_tsv else None,
    )
    write_report(result, Path(args.out))
    s = result["summary"]
    print("=" * 72)
    print("PEGASUS DATA MOVEMENT ANALYZER v0.5")
    print("=" * 72)
    print(f"tasks                 : {s['tasks']}")
    print(f"M_req                 : {s['m_req_mib']:.6f} MiB")
    print(f"M_obs                 : {s['m_obs_mib']:.6f} MiB")
    print(f"M_obs - M_req         : {s['observed_minus_required_mib']:.6f} MiB")
    print(f"M_req / M_obs         : {s['m_req_over_m_obs'] if s['m_req_over_m_obs'] is not None else 'NA'}")
    print(f"valid                 : {'yes' if s['valid'] else 'no'}")
    if s["errors"]:
        print(f"errors                : {s['errors']}")
    print(f"output                : {Path(args.out).resolve()}")
    return 0 if s["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
