from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

MIB = 1024 * 1024
TASK_RE = re.compile(r"data_task_ID0*(\d+)", re.I)

# These are execution/support artifacts, not scientific payload.
NON_SCIENTIFIC_BASENAMES = {
    "data_task",
    "pegasus-lite-common.sh",
}
NON_SCIENTIFIC_SUFFIXES = {
    ".meta", ".sh", ".log", ".out", ".err", ".json", ".properties", ".tar", ".gz", ".tgz"
}


@dataclass
class Task:
    task_id: int
    submit_file: str
    inputs: list[str]
    outputs: list[str]


@dataclass
class TransferRow:
    task: int
    logical_file: str
    direction: str
    source_location: str
    destination_location: str
    size_bytes: int
    size_mib: float
    evidence: str
    size_source: str


@dataclass
class RequiredRow:
    logical_file: str
    edge_type: str
    producer_task: str
    consumer_tasks: str
    source_location: str
    destination_location: str
    size_bytes: int
    size_mib: float
    required_bytes: int
    reason: str


def normalize_worker(value: str | None) -> str:
    value = (value or "").strip().strip('"')
    if "pegasus-worker1" in value:
        return "worker1"
    if "pegasus-worker2" in value:
        return "worker2"
    if "pegasus-master" in value:
        return "master"
    if "@" in value:
        value = value.split("@", 1)[1]
    return value or "UNKNOWN"


def extract_task_id(value: str | None) -> int | None:
    m = TASK_RE.search(value or "")
    return int(m.group(1)) if m else None


def _basename(value: str) -> str:
    # Condor submit syntax may contain macros such as $(wf_submit_dir)/foo.
    return Path(value.strip().strip('"')).name


def _split_condor_list(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_submit(path: Path) -> tuple[list[str], list[str]]:
    inputs: list[str] = []
    outputs: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = [x.strip() for x in line.split("=", 1)]
        key = key.lower()
        if key == "transfer_input_files":
            inputs = [_basename(x) for x in _split_condor_list(value)]
        elif key == "transfer_output_files":
            outputs = [_basename(x) for x in _split_condor_list(value)]
    return inputs, outputs


def discover_tasks(run_dir: Path) -> dict[int, Task]:
    tasks: dict[int, Task] = {}
    for sub in sorted(run_dir.rglob("data_task_ID*.sub")):
        task_id = extract_task_id(sub.name)
        if task_id is None:
            continue
        inputs, outputs = parse_submit(sub)
        tasks[task_id] = Task(task_id, str(sub), inputs, outputs)
    return tasks


def parse_meta_sizes(run_dir: Path) -> tuple[dict[str, int], dict[str, str]]:
    sizes: dict[str, int] = {}
    sources: dict[str, str] = {}
    for meta in sorted(run_dir.rglob("data_task_ID*.meta")):
        try:
            data = json.loads(meta.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        objects = data if isinstance(data, list) else [data]
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            name = obj.get("_id")
            attrs = obj.get("_attributes") or {}
            size = attrs.get("size")
            if not name or size is None:
                continue
            try:
                b = int(size)
            except (TypeError, ValueError):
                continue
            base = Path(str(name)).name
            sizes[base] = b
            sources[base] = f"meta:{meta}"
    return sizes, sources


def experiment_root(run_dir: Path) -> Path:
    s = str(run_dir.resolve())
    marker = "/luis/pegasus/"
    if marker in s:
        return Path(s.split(marker, 1)[0])
    # For fixtures and portable copies, allow run0001 sibling roots.
    p = run_dir.resolve()
    for parent in p.parents:
        if parent.name.startswith("distribution") or parent.name.startswith("pipeline") or parent.name.startswith("aggregation") or parent.name.startswith("redistribution") or parent.name.startswith("process"):
            return parent
    return p.parent


def find_physical_size(exp_root: Path, run_dir: Path, name: str) -> tuple[int | None, str | None]:
    preferred = [
        exp_root / "inputs" / name,
        exp_root / "input" / name,
        exp_root / "outputs" / name,
        exp_root / "output" / name,
        run_dir / name,
    ]
    for p in preferred:
        if p.is_file():
            return p.stat().st_size, str(p)

    seen: set[str] = set()
    candidates: list[tuple[int, str]] = []
    for root in [exp_root / "inputs", exp_root / "input", exp_root / "outputs", exp_root / "output", run_dir]:
        if not root.exists():
            continue
        try:
            for p in root.rglob(name):
                if not p.is_file() or str(p) in seen:
                    continue
                seen.add(str(p))
                candidates.append((p.stat().st_size, str(p)))
        except OSError:
            pass
    if candidates:
        candidates.sort(key=lambda x: x[1])
        return candidates[0]
    return None, None


def parse_classad_history(path: Path, run_dir: Path | None = None) -> dict[int, str]:
    """Parse `condor_history -long` output and recover scientific task placement.

    A record is accepted when it identifies a data_task_ID job. If run_dir is given,
    the record must also reference that run in Iwd/Cmd/Out/Err/UserLog.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    records = re.split(r"\n\s*\n", text)
    placement: dict[int, str] = {}
    run_s = str(run_dir.resolve()) if run_dir else None
    for record in records:
        fields: dict[str, str] = {}
        for line in record.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip().strip('"')
        identity = " ".join([
            fields.get("DAGNodeName", ""),
            fields.get("Cmd", ""),
        ])
        tid = extract_task_id(identity)
        if tid is None:
            continue
        if run_s:
            haystack = " ".join(fields.get(k, "") for k in ("Iwd", "Cmd", "Out", "Err", "UserLog"))
            # Portable/reconstructed fixtures may not have the same absolute root. If the
            # history clearly names a scientific task, allow it when no portable path can match.
            if run_s not in haystack and "run000" not in run_s:
                continue
        host = fields.get("LastRemoteHost") or fields.get("RemoteHost") or ""
        placement[tid] = normalize_worker(host)
    return placement


def placement_from_condor_history(run_dir: Path) -> dict[int, str]:
    try:
        cp = subprocess.run(
            ["condor_history", "-limit", "5000", "-af", "LastRemoteHost", "DAGNodeName", "Cmd", "Iwd"],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    placement: dict[int, str] = {}
    for line in cp.stdout.splitlines():
        if "data_task_ID" not in line:
            continue
        if str(run_dir) not in line:
            continue
        tid = extract_task_id(line)
        if tid is None:
            continue
        host = line.split()[0] if line.split() else ""
        placement[tid] = normalize_worker(host)
    return placement


def load_placement_tsv(path: Path) -> dict[int, str]:
    placement: dict[int, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            tid = extract_task_id(row.get("task") or row.get("cmd") or "")
            if tid is None:
                try:
                    tid = int(row.get("task_id", ""))
                except (TypeError, ValueError):
                    continue
            placement[tid] = normalize_worker(row.get("worker") or row.get("LastRemoteHost") or row.get("host"))
    return placement


def is_scientific_candidate(name: str, produced_names: set[str]) -> bool:
    base = Path(name).name
    if base in produced_names:
        return True
    if base in NON_SCIENTIFIC_BASENAMES:
        return False
    lower = base.lower()
    if lower.endswith(".dat"):
        return True
    if any(lower.endswith(s) for s in NON_SCIENTIFIC_SUFFIXES):
        return False
    return False


def resolve_sizes(run_dir: Path, scientific_names: Iterable[str]) -> tuple[dict[str, int], dict[str, str], list[str]]:
    sizes, sources = parse_meta_sizes(run_dir)
    exp = experiment_root(run_dir)
    errors: list[str] = []
    for name in sorted(set(scientific_names)):
        if name in sizes:
            continue
        size, source = find_physical_size(exp, run_dir, name)
        if size is None:
            errors.append(f"unknown size: {name}")
            continue
        sizes[name] = size
        sources[name] = f"physical:{source}"
    return sizes, sources, errors


def analyze_run(
    run_dir: Path,
    *,
    history_file: Path | None = None,
    placement_tsv: Path | None = None,
    master_name: str = "master",
) -> dict:
    run_dir = run_dir.resolve()
    tasks = discover_tasks(run_dir)
    errors: list[str] = []
    if not tasks:
        errors.append("no scientific data_task submit files found")

    produced_by: dict[str, int] = {}
    raw_inputs_by_task: dict[int, list[str]] = {}
    for tid, task in tasks.items():
        raw_inputs_by_task[tid] = list(task.inputs)
        for name in task.outputs:
            if name in produced_by and produced_by[name] != tid:
                errors.append(f"multiple producers: {name}")
            produced_by[name] = tid

    produced_names = set(produced_by)
    consumers: dict[str, list[int]] = defaultdict(list)
    scientific_inputs_by_task: dict[int, list[str]] = defaultdict(list)
    scientific_outputs_by_task: dict[int, list[str]] = defaultdict(list)

    for tid, task in tasks.items():
        for name in task.inputs:
            if is_scientific_candidate(name, produced_names):
                scientific_inputs_by_task[tid].append(name)
                consumers[name].append(tid)
        for name in task.outputs:
            if is_scientific_candidate(name, produced_names):
                scientific_outputs_by_task[tid].append(name)

    scientific_names = set(consumers) | set(produced_by)
    sizes, size_sources, size_errors = resolve_sizes(run_dir, scientific_names)
    errors.extend(size_errors)

    placement: dict[int, str] = {}
    placement_source: dict[int, str] = {}
    if placement_tsv and placement_tsv.exists():
        for tid, worker in load_placement_tsv(placement_tsv).items():
            placement[tid] = worker
            placement_source[tid] = f"tsv:{placement_tsv}"
    if history_file and history_file.exists():
        for tid, worker in parse_classad_history(history_file).items():
            if tid not in placement:
                placement[tid] = worker
                placement_source[tid] = f"history:{history_file}"
    for tid, worker in placement_from_condor_history(run_dir).items():
        if tid not in placement:
            placement[tid] = worker
            placement_source[tid] = "live:condor_history"

    for tid in tasks:
        if tid not in placement or placement[tid] == "UNKNOWN":
            placement[tid] = "UNKNOWN"
            placement_source.setdefault(tid, "missing")
            errors.append(f"unknown placement: task {tid}")

    # M_obs: every scientific file occurrence materialized by the task submit contract.
    observed: list[TransferRow] = []
    m_obs = 0
    for tid in sorted(tasks):
        task = tasks[tid]
        worker = placement[tid]
        for name in scientific_inputs_by_task[tid]:
            if name not in sizes:
                continue
            size = sizes[name]
            m_obs += size
            observed.append(TransferRow(
                tid, name, "master_to_worker", master_name, worker,
                size, size / MIB, task.submit_file, size_sources.get(name, ""),
            ))
        for name in scientific_outputs_by_task[tid]:
            if name not in sizes:
                continue
            size = sizes[name]
            m_obs += size
            observed.append(TransferRow(
                tid, name, "worker_to_master", worker, master_name,
                size, size / MIB, task.submit_file, size_sources.get(name, ""),
            ))

    # M_req: minimum payload that must CHANGE LOCATION while holding task placement fixed.
    required: list[RequiredRow] = []
    m_req = 0

    # External inputs originate on master. Ideal local reuse means one copy per distinct worker.
    for name in sorted(consumers):
        if name in produced_by or name not in sizes:
            continue
        by_dest: dict[str, list[int]] = defaultdict(list)
        for tid in consumers[name]:
            by_dest[placement[tid]].append(tid)
        for dest, tids in sorted(by_dest.items()):
            size = sizes[name]
            req = size if dest != master_name else 0
            m_req += req
            required.append(RequiredRow(
                name, "external_input", "MASTER", ",".join(map(str, sorted(tids))),
                master_name, dest, size, size / MIB, req,
                "input starts at master; count once for each destination location" if req else "already local",
            ))

    # Produced files: internal edge or final output.
    for name, producer_tid in sorted(produced_by.items()):
        if name not in sizes:
            continue
        size = sizes[name]
        src = placement[producer_tid]
        downstream = consumers.get(name, [])
        if not downstream:
            req = size if src != master_name else 0
            m_req += req
            required.append(RequiredRow(
                name, "final_output", str(producer_tid), "MASTER",
                src, master_name, size, size / MIB, req,
                "final result must return to master" if req else "already at final storage",
            ))
            continue

        by_dest: dict[str, list[int]] = defaultdict(list)
        for tid in downstream:
            by_dest[placement[tid]].append(tid)
        for dest, tids in sorted(by_dest.items()):
            req = size if dest != src else 0
            m_req += req
            required.append(RequiredRow(
                name, "intermediate", str(producer_tid), ",".join(map(str, sorted(tids))),
                src, dest, size, size / MIB, req,
                "producer and consumer locations differ" if req else "ideal local reuse: same worker",
            ))

    if m_obs > 0 and m_req > m_obs:
        errors.append("M_req > M_obs: inconsistent evidence/reference")
    if m_req > 0 and m_obs == 0:
        errors.append("M_req > 0 but M_obs = 0")

    return {
        "summary": {
            "run": str(run_dir),
            "tasks": len(tasks),
            "scientific_files": len(scientific_names),
            "m_req_bytes": m_req,
            "m_req_mib": m_req / MIB,
            "m_obs_bytes": m_obs,
            "m_obs_mib": m_obs / MIB,
            "observed_minus_required_bytes": m_obs - m_req,
            "observed_minus_required_mib": (m_obs - m_req) / MIB,
            "m_req_over_m_obs": (m_req / m_obs) if m_obs else None,
            "valid": not errors,
            "errors": " | ".join(errors),
            "definition": "M_req holds observed placement fixed and assumes ideal local reuse",
        },
        "tasks": [asdict(tasks[k]) for k in sorted(tasks)],
        "placement": [
            {"task": tid, "worker": placement[tid], "source": placement_source.get(tid, "")}
            for tid in sorted(placement)
        ],
        "file_sizes": [
            {"logical_file": name, "size_bytes": sizes[name], "size_mib": sizes[name] / MIB, "source": size_sources.get(name, "")}
            for name in sorted(sizes) if name in scientific_names
        ],
        "observed_transfers": [asdict(x) for x in observed],
        "required_movement": [asdict(x) for x in required],
    }


def write_tsv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = fields or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_report(result: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = result["summary"]
    write_tsv(out_dir / "summary.tsv", [summary])
    write_tsv(out_dir / "task_placement.tsv", result["placement"])
    write_tsv(out_dir / "file_sizes.tsv", result["file_sizes"])
    write_tsv(out_dir / "observed_transfers.tsv", result["observed_transfers"])
    write_tsv(out_dir / "required_movement.tsv", result["required_movement"])
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "PEGASUS DATA MOVEMENT ANALYZER v0.5",
        "=" * 72,
        f"Run      : {summary['run']}",
        f"Tasks    : {summary['tasks']}",
        f"M_req    : {summary['m_req_mib']:.6f} MiB",
        f"M_obs    : {summary['m_obs_mib']:.6f} MiB",
        f"M_obs-M_req: {summary['observed_minus_required_mib']:.6f} MiB",
        f"M_req/M_obs: {summary['m_req_over_m_obs'] if summary['m_req_over_m_obs'] is not None else 'NA'}",
        f"Valid    : {'YES' if summary['valid'] else 'NO'}",
        f"Errors   : {summary['errors'] or '-'}",
        "",
        "Definition of M_req:",
        "  Minimum scientific payload that must change location while preserving",
        "  the observed task placement and assuming ideal reuse of data already",
        "  present at a worker.",
        "",
        "Traceability files:",
        "  task_placement.tsv",
        "  file_sizes.tsv",
        "  observed_transfers.tsv",
        "  required_movement.tsv",
        "  summary.json",
    ]
    (out_dir / "REPORT.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
