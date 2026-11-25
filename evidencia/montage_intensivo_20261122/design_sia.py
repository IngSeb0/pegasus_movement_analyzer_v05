"""Keep the graph identical across all three conditions."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def plan(asset_names):
    asset_names = set(asset_names)
    inputs = sorted(n for n in asset_names if n.endswith(".fits"))
    assert 0 < len(inputs) <= 250 and "template.hdr" in asset_names
    tasks = [
        dict(task_id=f"P{i:02d}", assigned_worker=f"W{2 + (i - 1) % 3}", input_files=[name, "template.hdr"],
             output_files=[f"p{i:02d}.fits", f"p{i:02d}_area.fits"])
        for i, name in enumerate(inputs, 1)
    ]
    frames = [t["output_files"][0] for t in tasks]
    projected = [name for t in tasks for name in t["output_files"]]
    tasks.extend([
        dict(task_id="TABLE", assigned_worker="W1", input_files=frames, output_files=["images.tbl"]),
        dict(task_id="ADD", assigned_worker="W1", input_files=projected + ["images.tbl", "template.hdr"],
             output_files=["m101.fits", "m101_area.fits"]),
    ])
    return tasks


def specs(tasks, sizes):
    producers = {name: t["task_id"] for t in tasks for name in t["output_files"]}
    users = {}
    for task in tasks:
        for name in task["input_files"]:
            users.setdefault(name, []).append(task["task_id"])
    inputs = sorted(set(users) - set(producers))
    outputs = sorted(set(producers) - set(users))
    files = [
        dict(file_id=name, size_bytes=sizes[name], role="external" if name in inputs else
             "final" if name in outputs else "intermediate",
             producer_task=producers.get(name), consumer_tasks=users.get(name, []))
        for name in sorted(set(producers) | set(users))
    ]
    edges = [
        dict(producer_task=f["producer_task"], consumer_task=consumer, file_id=f["file_id"])
        for f in files if f["producer_task"] for consumer in f["consumer_tasks"]
    ]
    designs = {"MG-BASE": [], "MG-FINAL": [["TABLE", "ADD"]]}
    return {
        condition: dict(condition_id=condition, pattern="montage_m101", mode="CondorIO",
                        active_pool=["W1", "W2", "W3", "W4"], application="montage", files=files,
                        dag=dict(tasks=tasks, edges=edges, external_inputs=inputs, final_outputs=outputs),
                        groups=grouped + [[t["task_id"]] for t in tasks
                                         if not any(t["task_id"] in group for group in grouped)])
        for condition, grouped in designs.items()
    }


def preflight(root):
    assets = root / "montage_assets"
    tasks = plan(p.name for p in assets.iterdir())
    entries = json.loads((root / "ENTRADAS.json").read_text())
    selected = {entry["nombre"] for entry in entries}
    assert selected == {asset.name for asset in assets.glob("*.fits")}
    for entry in entries:
        path = assets / entry["nombre"]
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        assert path.stat().st_size == entry["bytes"] and digest == entry["sha256"], path
    work = root / "reference"
    work.mkdir()
    sizes = {}
    for name in sorted(set(n for t in tasks for n in t["input_files"] if (assets / n).is_file())):
        shutil.copyfile(assets / name, work / name)
        sizes[name] = (work / name).stat().st_size
    receipts = []
    for task in tasks:
        command = [sys.executable, str(assets / "montage_task.py"), "--task-id", task["task_id"]]
        for name in task["input_files"]:
            command.extend(["--input", name, str(sizes[name])])
        for name in task["output_files"]:
            command.extend(["--output", name, "0"])
        result = subprocess.run(command, cwd=work, text=True, capture_output=True, timeout=300)
        if result.returncode:
            raise RuntimeError(f"{task['task_id']}: {result.stderr[-2000:]}")
        receipt = json.loads(result.stdout.strip().splitlines()[-1])
        receipts.append(receipt)
        for record in receipt["artifacts"]:
            sizes[record["file"]] = record["bytes"]
    designs = specs(tasks, sizes)
    (root / "SPECS.json").write_text(json.dumps(designs, indent=2))
    (root / "REFERENCE.json").write_text(json.dumps(receipts, indent=2))
    print(f"Verified {len(tasks)} local scientific operations and {len(sizes)} file sizes.")


if __name__ == "__main__":
    preflight(Path(__file__).resolve().parent)
