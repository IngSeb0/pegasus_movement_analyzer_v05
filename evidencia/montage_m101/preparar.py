"""Stage immutable inputs and tested experimental infrastructure for the new study."""

import base64
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile

from design import plan, specs

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
PAYLOAD = BASE / "payload"
PREVIOUS = ROOT / "campana_dme_20261108"
TUTORIAL = ROOT / "montaje_m101_20261111_entrada.tar.gz"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Cannot adapt verified source at {old[:60]}")
    return source.replace(old, new)


def copy_text(source, destination):
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def build():
    assets = PAYLOAD / "montage_assets"
    runtime = PAYLOAD / "runtime"
    core = PAYLOAD / "core" / "pegasus_movement"
    for directory in (assets, runtime, core):
        directory.mkdir(parents=True, exist_ok=True)
    with tarfile.open(TUTORIAL) as archive:
        for member in archive:
            if not member.isfile() or not member.name.endswith((".fits", "template.hdr")):
                continue
            with archive.extractfile(member) as data, (assets / Path(member.name).name).open("wb") as destination:
                shutil.copyfileobj(data, destination)
    graph = plan(p.name for p in assets.iterdir())
    wheel, = (ROOT / "pruebas_cierre_sin_cf_20261031/preparacion_montage").glob("montagepy-2.3.0-*.whl")
    executable = (BASE / "mosaic_task.py").read_text(encoding="utf-8")
    (assets / "montage_task.py").write_text(
        executable + f"\nWHEEL = {base64.b64encode(wheel.read_bytes())!r}\n\nif __name__ == '__main__':\n    main()\n",
        encoding="utf-8", newline="\n")
    for source in (ROOT / "vm_repo/pegasus_movement").glob("*.py"):
        shutil.copyfile(source, core / source.name)
    assert len(list(core.glob("*.py"))) == 16
    for name in ["campaign_task.py", "generate_workflow.py", "inspect_plan.py", "audit_native.py"]:
        copy_text(PREVIOUS / "payload/runtime" / name, runtime / name)
    for name in ["design.py", "measure.py"]:
        copy_text(BASE / name, PAYLOAD / name)
    old_runner = (PREVIOUS / "payload/runtime/run_study.py").read_text(encoding="utf-8")
    old_runner = old_runner[:old_runner.index("def main():")]
    substitutions = [
        ("assert len(ledger)<76 and sum(r['sessionStart']==s['startedAtUtc']for r in ledger)<40",
         "assert len(ledger)<s['maximumNewWorkflows']"),
        ("prospective_study='20261108'", "prospective_study='montage-m101-20261111'"),
        ("with tarfile.open(out,'w:xz')as t:", "with tarfile.open(out,'w:xz',preset=1)as t:"),
        ("time.time()+420", "time.time()+800"),
        ("expected=read(ROOT/'PREDICTIONS.json')[row['condition']]",
         "expected=read(ROOT/'PLAN_ACCOUNTS.json')[row['condition']]"),
    ]
    for old, new in substitutions:
        old_runner = replace_once(old_runner, old, new)
    (runtime / "run_study.py").write_text(old_runner, encoding="utf-8", newline="\n")
    sys.path.insert(0, str(runtime))
    from generate_workflow import validate_condition
    sizes = {name: 1 for task in graph for name in task["input_files"] + task["output_files"]}
    for condition in specs(graph, sizes).values():
        review = validate_condition(condition, {"W1": "dme-worker1", "W2": "dme-worker2", "master": "dme-master"})
        assert review["task_count"] == 12 and review["final_outputs"] == ["m101.fits", "m101_area.fits"]
    hashes = {p.relative_to(PAYLOAD).as_posix(): digest(p)
              for p in sorted(PAYLOAD.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name != "HASHES.json"}
    (PAYLOAD / "HASHES.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    with tarfile.open(BASE / "payload.tar.gz", "w:gz", compresslevel=3) as tar:
        for name in [*hashes, "HASHES.json"]:
            tar.add(PAYLOAD / name, arcname=name)
    receipt = dict(offlineChecksPassed=True, tutorialSha256=digest(TUTORIAL), wheelSha256=digest(wheel),
                   payloadSha256=digest(BASE / "payload.tar.gz"), tasks=12, conditions=3, coreFiles=16)
    (BASE / "PREPARATION.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    cloud = (PREVIOUS / "cloud.py").read_text(encoding="utf-8")
    cloud = replace_once(cloud, "timedelta(hours=3)", "timedelta(minutes=90)")
    cloud = replace_once(cloud, "timedelta(minutes=135)", "timedelta(minutes=60)")
    cloud = replace_once(cloud, "maximumNewWorkflows=40", "maximumNewWorkflows=3")
    cloud = replace_once(cloud, "User explicitly authorized VM experiments on 2026-11-08; scope in campaign protocol.",
                         "Montage M101 complete workflow requested on 2026-11-11; scope in PROTOCOLO.md.")
    (BASE / "cloud.py").write_text(cloud, encoding="utf-8", newline="\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    build()
