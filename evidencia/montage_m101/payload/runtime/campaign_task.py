#!/usr/bin/env python3
"""One invariant, bounded-memory synthetic file task for the DME campaign.

This program reads every input completely and writes every declared output.
Its stdout is application provenance, never proof of network transfer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROGRAM_VERSION = "1.0"
BLOCK_BYTES = 1024 * 1024
LFN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def validate_lfn(value: str) -> str:
    if not isinstance(value, str) or not LFN_PATTERN.fullmatch(value) or value in {".", ".."}:
        raise ValueError("LFNs must be simple relative filenames: " + repr(value))
    return value


def byte_size(value) -> int:
    if isinstance(value, bool):
        raise ValueError("A byte size cannot be boolean")
    result = int(value)
    if result < 0 or (not isinstance(value, int) and str(result) != str(value)):
        raise ValueError("Byte sizes must be nonnegative decimal integers")
    return result


def read_payload(path: Path, expected_bytes: int) -> dict:
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(BLOCK_BYTES)
            if not block:
                break
            count += len(block)
            digest.update(block)
    if count != expected_bytes:
        raise ValueError(f"Input {path.name}: read {count} bytes; declared {expected_bytes}")
    return {"lfn": path.name, "bytes_read": count, "sha256": digest.hexdigest()}


def write_payload(path: Path, size_bytes: int, seed: bytes) -> dict:
    """Write exact size with a deterministic 1 MiB block; no sparse/truncate shortcut."""
    block = hashlib.shake_256(seed).digest(BLOCK_BYTES)
    digest = hashlib.sha256()
    remaining = size_bytes
    with path.open("wb") as stream:
        while remaining:
            piece = block if remaining >= BLOCK_BYTES else block[:remaining]
            written = stream.write(piece)
            if written != len(piece):
                raise OSError(f"Short output write for {path}")
            digest.update(piece)
            remaining -= written
    if path.stat().st_size != size_bytes:
        raise OSError(f"Output size mismatch for {path}")
    return {"lfn": path.name, "bytes_written": size_bytes, "sha256": digest.hexdigest()}


def run_task(task_id: str, inputs, outputs) -> dict:
    input_specs = [(validate_lfn(name), byte_size(size)) for name, size in inputs]
    output_specs = [(validate_lfn(name), byte_size(size)) for name, size in outputs]
    for label, specs in (("input", input_specs), ("output", output_specs)):
        names = [name for name, _ in specs]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate {label} LFN")
    if set(name for name, _ in input_specs) & set(name for name, _ in output_specs):
        raise ValueError("A task cannot overwrite its input LFN")
    if not output_specs:
        raise ValueError("At least one scientific output is required")
    input_records = [read_payload(Path(name), size) for name, size in input_specs]
    identity = json.dumps({"program_version": PROGRAM_VERSION, "task_id": task_id,
                           "inputs": input_records}, sort_keys=True, separators=(",", ":"))
    output_records = []
    for name, size in output_specs:
        seed = (identity + "\noutput=" + name).encode("utf-8")
        output_records.append(write_payload(Path(name), size, seed))
    return {"record_type": "application_file_io_provenance_not_transfer_evidence",
            "program_version": PROGRAM_VERSION, "task_id": task_id,
            "block_bytes": BLOCK_BYTES, "inputs": input_records, "outputs": output_records}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--input", nargs=2, action="append", default=[], metavar=("LFN", "BYTES"))
    parser.add_argument("--output", nargs=2, action="append", required=True, metavar=("LFN", "BYTES"))
    args = parser.parse_args(argv)
    try:
        result = run_task(args.task_id, args.input, args.output)
    except (OSError, ValueError) as error:
        print(json.dumps({"task_id": args.task_id, "status": "failed", "error": str(error)}),
              file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
