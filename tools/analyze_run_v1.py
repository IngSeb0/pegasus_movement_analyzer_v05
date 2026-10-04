#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

if str(HERE) not in sys.path:
    sys.path.insert(
        0,
        str(HERE),
    )

from pegasus_movement.analyzer_v1 import (
    analyze_run_v1,
    overall_status,
)
from pegasus_movement.reporting import (
    exit_code_for_status,
    write_reports,
)


def analyzer_version() -> str:
    try:
        result = subprocess.run(
            [
                "git",
                "rev-parse",
                "--short",
                "HEAD",
            ],
            cwd=HERE,
            check=True,
            capture_output=True,
            text=True,
        )

        return (
            "v1@"
            + result.stdout.strip()
        )

    except Exception:
        return "v1@unknown"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pegasus Data Movement Analyzer v1"
        )
    )

    parser.add_argument(
        "--run",
        required=True,
    )

    parser.add_argument(
        "--history-file",
        required=True,
    )

    parser.add_argument(
        "--out",
        required=True,
    )

    args = parser.parse_args()

    run = analyze_run_v1(
        Path(args.run),
        history_file=Path(
            args.history_file
        ),
    )

    write_reports(
        run,
        Path(args.out),
        verifications=run.verifications,
        diagnostics=run.diagnostics,
        analyzer_version=(
            analyzer_version()
        ),
    )

    status = overall_status(
        run
    )

    print("=" * 72)
    print(
        "PEGASUS DATA MOVEMENT ANALYZER v1"
    )
    print("=" * 72)
    print(
        f"run                    : "
        f"{run.run_id}"
    )
    print(
        f"workflow               : "
        f"{run.workflow_name}"
    )
    print(
        f"status                 : "
        f"{status.value}"
    )

    metric = run.metric_result

    if metric is not None:
        print(
            f"RequiredMovement       : "
            f"{metric.required_movement_bytes} B"
        )
        print(
            f"DeclaredMovement       : "
            f"{metric.declared_movement_bytes} B"
        )
        print(
            f"Coverage               : "
            f"{metric.coverage}"
        )
        print(
            f"ObservedMovement       : "
            f"{metric.observed_movement_bytes}"
        )
        print(
            f"DME                    : "
            f"{metric.dme}"
        )

    else:
        print(
            "metrics                : N/A"
        )

    if run.diagnostics:
        print(
            f"diagnostics            : "
            f"{len(run.diagnostics)}"
        )

        for diagnostic in (
            run.diagnostics[:10]
        ):
            print(
                "  "
                f"{diagnostic.status.value} / "
                f"{diagnostic.reason_code.value}: "
                f"{diagnostic.message}"
            )

    print(
        f"output                 : "
        f"{Path(args.out).resolve()}"
    )

    return exit_code_for_status(
        status
    )


if __name__ == "__main__":
    raise SystemExit(main())
