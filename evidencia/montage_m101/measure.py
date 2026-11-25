"""Review all three native plans before the first submission."""

import collections
import fcntl
import hashlib
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "runtime"))
import run_study as runner


CONDITIONS = ["M101-BASE", "M101-PROJ", "M101-FINAL"]
ROWS = [dict(id=condition, condition=condition, block=1, phase="main") for condition in CONDITIONS]


def plan_all():
    runner.frozen()
    runner.idle()
    specs = runner.read(ROOT / "SPECS.json")
    accounts = {}
    for row in ROWS:
        name = row["id"]
        _, _, evidence, _, spec, _ = runner.prepare(row)
        review = runner.read(evidence / "PLAN_REVIEW.json")
        files = {f["file_id"]: f for f in spec["files"]}
        placement = {task["task_id"]: task["assigned_worker"] for task in spec["dag"]["tasks"]}
        required = 0
        for f in files.values():
            origin = placement[f["producer_task"]] if f["producer_task"] else "master"
            destinations = {placement[task] for task in f["consumer_tasks"]} - {origin}
            if f["role"] == "final" or (f["producer_task"] and destinations):
                destinations.add("master")
            required += len(destinations) * f["size_bytes"]
        directions = collections.Counter(
            (name, direction, job["worker"])
            for job in review["jobs"] for direction in ("input", "output")
            for name in job["scientific_files"][direction]
        )
        observed = sum(files[file]["size_bytes"] * count for (file, _, _), count in directions.items())
        assert observed == review["planned_scientific_bytes"]
        accounts[name] = dict(required=required, observed=observed,
                              jobs=len(review["jobs"]), directions=[[*key, n] for key, n in sorted(directions.items())])
    baseline, projections, final = (accounts[name] for name in CONDITIONS)
    assert [a["jobs"] for a in accounts.values()] == [12, 11, 11]
    assert len({a["required"] for a in accounts.values()}) == 1
    def difference(other):
        base = collections.Counter({tuple(row[:3]): row[3] for row in baseline["directions"]})
        variant = collections.Counter({tuple(row[:3]): row[3] for row in other["directions"]})
        assert not (variant - base), "The variant introduced a scientific delivery"
        return base - variant
    assert difference(projections) == {("template.hdr", "input", "dme-worker2"): 1}
    expected = {(f"p{i:02d}.fits", "input", "dme-worker1"): 1 for i in range(1, 11)}
    expected["images.tbl", "input", "dme-worker1"] = 1
    result = difference(final)
    assert result == expected or result == {**expected, ("images.tbl", "output", "dme-worker1"): 1}
    assert final["observed"] < projections["observed"] < baseline["observed"]
    runner.save(ROOT / "PLAN_ACCOUNTS.json", accounts)
    runner.save(ROOT / "FROZEN_DESIGN.json", {name: runner.sha(ROOT / name)
                                            for name in ("SPECS.json", "PLAN_ACCOUNTS.json", "REFERENCE.json")})
    print({name: {k: v for k, v in row.items() if k != "directions"} for name, row in accounts.items()}, flush=True)


def digest_fits(path):
    cards = {}
    with path.open("rb") as stream:
        ended = False
        while not ended:
            block = stream.read(2880)
            assert len(block) == 2880
            for offset in range(0, 2880, 80):
                card = block[offset:offset + 80].decode("ascii")
                key = card[:8].strip()
                if key == "END":
                    ended = True
                    break
                if card[8:10] == "= " and key not in {"DATE", "CHECKSUM", "DATASUM"}:
                    cards[key] = card[10:].strip()
        pixels = hashlib.file_digest(stream, "sha256").hexdigest()
    assert cards["NAXIS"].split("/")[0].strip() == "2"
    return dict(cards=cards, pixelHash=pixels)


def verify_outputs():
    reference = {file: digest_fits(ROOT / "reference" / file) for file in ("m101.fits", "m101_area.fits")}
    observed = {}
    for name in CONDITIONS:
        folder = ROOT / "cases" / name / "plans" / name / "outputs"
        observed[name] = {file: digest_fits(folder / file) for file in reference}
        assert observed[name] == reference, "Final FITS image or coverage map differs"
    runner.save(ROOT / "FITS_EQUIVALENCE.json", dict(matches=True, reference=reference, conditions=observed))


def run_all():
    for name, digest in runner.read(ROOT / "FROZEN_DESIGN.json").items():
        assert runner.sha(ROOT / name) == digest
    for row in ROWS:
        results = runner.read(ROOT / "RESULTS.json") if (ROOT / "RESULTS.json").exists() else []
        if row["id"] not in {r["id"] for r in results}:
            runner.execute(row)
    verify_outputs()
    runner.save(ROOT / "COMPLETE.json", dict(accepted=3, queue=runner.command(["condor_q", "-allusers", "-json"])))


if __name__ == "__main__":
    with (ROOT / "experiment.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            {"plan": plan_all, "run": run_all}[sys.argv[1]]()
        except Exception as error:
            runner.save(ROOT / "STOPPED.json", dict(error=str(error), traceback=traceback.format_exc()))
            raise
