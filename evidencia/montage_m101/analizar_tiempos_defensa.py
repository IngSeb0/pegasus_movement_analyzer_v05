"""Locate timing differences in the preserved DAGMan events."""

import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parent
SYNTHETIC = ROOT.parent / "validacion_cinco_patrones_20261110" / "evidence"
MONTAGE = ROOT / "evidence" / "capsules"


def read_jobstate(path):
    with tarfile.open(path, "r:xz") as archive:
        for member in archive:
            if member.name.endswith("/jobstate.log"):
                return archive.extractfile(member).read().decode().splitlines()
    raise ValueError(f"Missing jobstate.log in {path}")


def timing(path, expected_jobs):
    rows = [line.split() for line in read_jobstate(path) if line.strip()]
    start, = (int(row[0]) for row in rows if "DAGMAN_STARTED" in row)
    end, = (int(row[0]) for row in rows if "DAGMAN_FINISHED" in row)
    scientific = [row for row in rows if row[1].startswith(("campaign_task_", "merge_group_"))]
    event_times = {}
    for event in ("SUBMIT", "EXECUTE", "JOB_TERMINATED"):
        event_times[event] = {row[1]: int(row[0]) - start for row in scientific if row[2] == event}
        if len(event_times[event]) != expected_jobs:
            raise ValueError(f"{path.name}: unexpected {event} nodes {list(event_times[event])}")
    submitted = min(event_times["SUBMIT"].values())
    started = min(event_times["EXECUTE"].values())
    last = max(event_times["JOB_TERMINATED"].values())
    return dict(first_submit_s=submitted, first_execute_s=started, last_terminated_s=last,
                finish_s=end-start, wait_to_first_job_s=started-submitted,
                scientific_window_s=last-started, after_last_job_s=end-start-last,
                jobs=event_times)


def main():
    cases = [(f"{pattern}-W{workers}", SYNTHETIC, 6)
             for pattern in ("PROCESS", "PIPELINE", "AGGREGATION", "DISTRIBUTION", "REDISTRIBUTION")
             for workers in (2, 4)]
    cases.extend((name, MONTAGE, jobs) for name, jobs in
                 (("M101-BASE", 12), ("M101-PROJ", 11), ("M101-FINAL", 11)))
    result = {name: timing(folder / (name + ".tar.xz"), jobs) for name, folder, jobs in cases}
    (ROOT / "TIEMPOS_DEFENSA.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({name: {key: value for key, value in row.items() if key != "jobs"}
                      for name, row in result.items()}, indent=2))


if __name__ == "__main__":
    main()
