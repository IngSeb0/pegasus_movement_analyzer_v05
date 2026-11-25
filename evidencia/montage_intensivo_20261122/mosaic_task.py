#!/usr/bin/env python3
"""MontagePy scientific task, identical in the three execution plans."""

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--input", nargs=2, action="append", required=True)
    parser.add_argument("--output", nargs=2, action="append", required=True)
    args = parser.parse_args()
    for name, size in args.input:
        if Path(name).name != name or Path(name).stat().st_size != int(size):
            raise ValueError(f"Unexpected input {name}")
    runtime = Path(".toolkit-" + args.task_id)
    runtime.mkdir()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(WHEEL))) as wheel:
        wheel.extractall(runtime)
    sys.path.insert(0, str(runtime.resolve()))
    from MontagePy.main import mAdd, mImgtbl, mProjectPP

    if args.task_id.startswith("P"):
        frame = next(name for name, _ in args.input if name.endswith(".fits"))
        output = next(name for name, _ in args.output if not name.endswith("_area.fits"))
        result = mProjectPP(frame, output, "template.hdr")
    else:
        frames = Path(".frames-" + args.task_id)
        frames.mkdir()
        for name, _ in sorted(args.input):
            if name.endswith(".fits"):
                (frames / name).symlink_to(Path(name).resolve())
        if args.task_id == "TABLE":
            result = mImgtbl(str(frames), "images.tbl")
            if int(result.get("count", -1)) != len(args.input):
                raise ValueError(f"Unexpected image table: {result}")
        elif args.task_id == "ADD":
            result = mAdd(str(frames), "images.tbl", "template.hdr", "m101.fits")
        else:
            raise ValueError(args.task_id)
    if int(result.get("status", -1)) != 0:
        raise RuntimeError(result)
    shutil.rmtree(runtime)
    artifacts = []
    for name, expected in args.output:
        path = Path(name)
        size = path.stat().st_size
        if int(expected) != 0 and size != int(expected):
            raise ValueError(f"Unexpected output size for {name}")
        with path.open("rb") as stream:
            artifacts.append(dict(file=name, bytes=size, sha256=hashlib.file_digest(stream, "sha256").hexdigest()))
    print(json.dumps(dict(task=args.task_id, artifacts=artifacts, montage=result), default=str))

