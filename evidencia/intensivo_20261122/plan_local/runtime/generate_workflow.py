#!/usr/bin/env python3
"""Prepare one CondorIO run using the independent declarative oracle and Pegasus API.

No planner, submit command, SSH, Analyzer, or expected-volume-as-evidence logic.
Pegasus is imported lazily. --validate-only uses the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from campaign_task_fma import PROGRAM_VERSION, byte_size, validate_lfn, write_payload

GENERATOR_VERSION = "fma_v1"
HOST_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
ID_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
PROPERTIES = "pegasus.data.configuration=condorio\npegasus.selector.site=RoundRobin\n"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_worker_map(value) -> dict:
    if isinstance(value, dict):
        data = value
    else:
        text = str(value)
        if text.lstrip().startswith("{"):
            data = json.loads(text)
        else:
            path = Path(text[1:] if text.startswith("@") else text)
            data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not data:
        raise ValueError("worker-map must be a nonempty JSON object")
    for key, machine in data.items():
        if not isinstance(key, str) or not isinstance(machine, str) or not HOST_PATTERN.fullmatch(machine):
            raise ValueError("worker-map values must be exact hostname/TARGET.Machine strings")
    return dict(data)


def load_condition(oracle, condition_id: str) -> dict:
    document = json.loads(Path(oracle).read_text(encoding="utf-8-sig"))
    matches = [c for c in document.get("conditions", []) if c.get("condition_id") == condition_id]
    if len(matches) != 1:
        raise ValueError("Condition must occur exactly once in oracle conditions[]: " + condition_id)
    # Deliberate whitelist: mathematical predictions never become execution evidence.
    raw = matches[0]
    return {"condition_id": raw["condition_id"], "pattern": raw["pattern"],
            "mode": raw["mode"], "active_pool": list(raw["active_pool"]),
            "dag": raw["dag"],
            "files": [{key: f[key] for key in ("file_id", "size_bytes", "role",
                                               "producer_task", "consumer_tasks")}
                      for f in raw["files"]]}


def validate_condition(condition: dict, worker_map: dict) -> dict:
    if condition.get("mode") != "CondorIO":
        raise ValueError("This generator only implements CondorIO, not NonSharedFS or SharedFS")
    cid = condition["condition_id"]
    if not ID_PATTERN.fullmatch(cid):
        raise ValueError("Invalid condition identifier")
    pool = condition["active_pool"]
    if not pool or len(pool) != len(set(pool)):
        raise ValueError("Active pool must be nonempty and contain no duplicates")
    if any(alias not in worker_map for alias in pool):
        raise ValueError("worker-map is missing an active worker")
    if len({worker_map[alias].lower() for alias in pool}) != len(pool):
        raise ValueError("Active worker aliases must map to distinct machines")
    if "master" in worker_map and worker_map["master"].lower() in {
            worker_map[alias].lower() for alias in pool}:
        raise ValueError("The master must not also be a compute worker")
    tasks = condition["dag"]["tasks"]
    ids = [t["task_id"] for t in tasks]
    if not ids or len(ids) != len(set(ids)) or any(not ID_PATTERN.fullmatch(i) for i in ids):
        raise ValueError("Task IDs must be unique nonempty identifiers")
    files = condition["files"]
    names = [validate_lfn(f["file_id"]) for f in files]
    if len(names) != len(set(names)):
        raise ValueError("File identities must be unique")
    by_file = {f["file_id"]: f for f in files}
    produced, consumed = {}, {name: [] for name in names}
    for f in files:
        f["size_bytes"] = byte_size(f["size_bytes"])
    for t in tasks:
        if not isinstance(t.get("flops"), int) or isinstance(t["flops"], bool) or t["flops"] < 0 or t["flops"] % 2:
            raise ValueError("Every task requires an even nonnegative FLOP count")
        if t["assigned_worker"] not in pool:
            raise ValueError("Task assigned outside active pool: " + t["task_id"])
        for field in ("input_files", "output_files"):
            if len(t[field]) != len(set(t[field])):
                raise ValueError("Repeated file declaration within task")
            if any(name not in by_file for name in t[field]):
                raise ValueError("Task refers to undeclared scientific file")
        if not t["output_files"] or set(t["input_files"]) & set(t["output_files"]):
            raise ValueError("Tasks require outputs and must not overwrite their inputs")
        for name in t["output_files"]:
            if name in produced:
                raise ValueError("Multiple producers for " + name)
            produced[name] = t["task_id"]
        for name in t["input_files"]:
            consumed[name].append(t["task_id"])
    inferred_edges = {(produced[name], user, name) for name in names if name in produced
                      for user in consumed[name]}
    declared_edges_list = [(e["producer_task"], e["consumer_task"], e["file_id"])
                           for e in condition["dag"]["edges"]]
    if len(declared_edges_list) != len(set(declared_edges_list)) or set(declared_edges_list) != inferred_edges:
        raise ValueError("DAG edges do not match task/file producer-consumer relationships")
    for f in files:
        name = f["file_id"]
        if f["producer_task"] != produced.get(name) or set(f["consumer_tasks"]) != set(consumed[name]):
            raise ValueError("File declarations disagree with task relationships: " + name)
        if name not in produced and not consumed[name]:
            raise ValueError("Unused external scientific file")
    external = sorted(name for name in names if name not in produced)
    final = sorted(name for name in names if name in produced and not consumed[name])
    if set(external) != set(condition["dag"]["external_inputs"]) or set(final) != set(condition["dag"]["final_outputs"]):
        raise ValueError("External-input/final-output sets do not match the DAG")
    # Kahn ordering catches cycles without executing or importing Pegasus.
    parents = {task_id: set() for task_id in ids}
    children = {task_id: set() for task_id in ids}
    for producer, consumer, _ in inferred_edges:
        parents[consumer].add(producer)
        children[producer].add(consumer)
    ready = sorted(task_id for task_id in ids if not parents[task_id])
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for child in sorted(children[node]):
            parents[child].discard(node)
            if not parents[child] and child not in order and child not in ready:
                ready.append(child)
        ready.sort()
    if len(order) != len(ids):
        raise ValueError("Workflow must be acyclic")
    return {"condition_id": cid, "mode": "CondorIO", "task_count": len(tasks),
            "scientific_file_count": len(files), "external_inputs": external,
            "final_outputs": final, "topological_order": order,
            "active_pool": list(pool), "requirements": {
                t["task_id"]: f'TARGET.Machine == {json.dumps(worker_map[t["assigned_worker"]])}'
                for t in tasks}, "status": "declarative_structure_validated_not_executed"}


def build_workflow(condition, root, worker_map, *, replica=1, oracle_sha256=None):
    """Return a Pegasus Workflow; never plan or submit. Requires installed Pegasus API."""
    validate_condition(condition, worker_map)
    from Pegasus.api import (Arch, Directory, File, FileServer, Job, Operation, OS,
                             ReplicaCatalog, Site, SiteCatalog, Transformation,
                             TransformationCatalog, Workflow)

    root = Path(root).resolve()
    name = f'dme-six-20261110-{condition["condition_id"].lower()}-r{replica:02d}'
    workflow = Workflow(name, infer_dependencies=False)
    local = Site("local", arch=Arch.X86_64, os_type=OS.LINUX).add_directories(
        Directory(Directory.SHARED_SCRATCH, root / "scratch", shared_file_system=False)
            .add_file_servers(FileServer((root / "scratch").as_uri(), Operation.ALL)),
        Directory(Directory.LOCAL_STORAGE, root / "outputs", shared_file_system=False)
            .add_file_servers(FileServer((root / "outputs").as_uri(), Operation.ALL)),
    )
    condorpool = (Site("condorpool", arch=Arch.X86_64, os_type=OS.LINUX)
                  .add_pegasus_profile(style="condor", auxillary_local=True)
                  .add_condor_profile(universe="vanilla", request_cpus="1", request_memory="256"))
    workflow.add_site_catalog(SiteCatalog().add_sites(local, condorpool))
    file_objects = {f["file_id"]: File(f["file_id"]) for f in condition["files"]}
    by_file = {f["file_id"]: f for f in condition["files"]}
    replicas = ReplicaCatalog()
    for name in condition["dag"]["external_inputs"]:
        replicas.add_replica("local", file_objects[name], root / "inputs" / name)
    kernel_file = File("fma_kernel")
    replicas.add_replica("local", kernel_file, root / "bin" / "fma_kernel")
    workflow.add_replica_catalog(replicas)
    program = Transformation("campaign_task", site="local", pfn=root / "bin" / "campaign_task.py",
                             is_stageable=True, arch=Arch.X86_64, os_type=OS.LINUX)
    workflow.add_transformation_catalog(TransformationCatalog().add_transformations(program))
    jobs = {}
    for spec in condition["dag"]["tasks"]:
        job = Job(program, _id=spec["task_id"])
        job.add_args("--task-id", spec["task_id"], "--flops", str(spec["flops"]))
        for name in spec["input_files"]:
            job.add_args("--input", file_objects[name], str(by_file[name]["size_bytes"]))
            job.add_inputs(file_objects[name], bypass_staging=False)
        for name in spec["output_files"]:
            job.add_args("--output", file_objects[name], str(by_file[name]["size_bytes"]))
            job.add_outputs(file_objects[name], stage_out=name in condition["dag"]["final_outputs"],
                            register_replica=False)
        machine = worker_map[spec["assigned_worker"]]
        job.add_condor_profile(requirements=f"TARGET.Machine == {json.dumps(machine)}",
                               request_cpus="1", request_memory="256")
        job.add_metadata(task_id=spec["task_id"], condition_id=condition["condition_id"],
                         replica=str(replica), pattern=condition["pattern"],
                         controlled_worker=spec["assigned_worker"], target_machine=machine,
                         flops=str(spec["flops"]),
                         scientific_inputs=json.dumps(spec["input_files"]),
                         scientific_outputs=json.dumps(spec["output_files"]))
        workflow.add_jobs(job)
        jobs[spec["task_id"]] = job
    # Several files can imply the same task edge; add each parent-child pair once.
    for producer, consumer in sorted({(e["producer_task"], e["consumer_task"])
                                     for e in condition["dag"]["edges"]}):
        workflow.add_dependency(jobs[producer], children=[jobs[consumer]])
    workflow.add_metadata(condition_id=condition["condition_id"], pattern=condition["pattern"],
                          replica=str(replica), data_configuration="condorio",
                          program_version=PROGRAM_VERSION,
                          oracle_sha256=oracle_sha256 or "not_supplied_to_builder",
                          scientific_file_sizes_bytes=json.dumps({f["file_id"]: f["size_bytes"]
                                                                   for f in condition["files"]}, sort_keys=True))
    return workflow


def prepare_run(condition, root, worker_map, replica, oracle_path):
    root = Path(root).resolve()
    validation = validate_condition(condition, worker_map)
    own_files = [root / "workflow.yml", root / "pegasus.properties", root / "meta.json",
                 root / "bin" / "campaign_task.py"]
    own_files += [root / "inputs" / name for name in condition["dag"]["external_inputs"]]
    collisions = [str(p) for p in own_files if p.exists() or p.is_symlink()]
    if collisions:
        raise FileExistsError("Refusing to overwrite generated artifacts: " + ", ".join(collisions))
    # Check API availability and construct the workflow before creating run artifacts.
    oracle_digest = sha256_path(Path(oracle_path))
    workflow = build_workflow(condition, root, worker_map, replica=replica, oracle_sha256=oracle_digest)
    for name in ("bin", "inputs", "scratch", "outputs"):
        (root / name).mkdir(parents=True, exist_ok=True)
    program_bytes = Path(__file__).with_name("campaign_task_fma.py").read_bytes().replace(b"\r\n", b"\n")
    program_path = root / "bin" / "campaign_task.py"
    with program_path.open("xb") as stream:
        stream.write(program_bytes)
    program_path.chmod(0o755)
    kernel_source = Path(__file__).with_name("fma_kernel")
    kernel_path = root / "bin" / "fma_kernel"
    with kernel_path.open("xb") as stream:
        stream.write(kernel_source.read_bytes())
    kernel_path.chmod(0o755)
    by_file = {f["file_id"]: f for f in condition["files"]}
    input_artifacts = []
    for name in condition["dag"]["external_inputs"]:
        record = write_payload(root / "inputs" / name, by_file[name]["size_bytes"],
                               ("initial-scientific-input-v1:" + name).encode("utf-8"))
        record["path"] = str(root / "inputs" / name)
        record["evidence_role"] = "generated_initial_file_not_transfer_evidence"
        input_artifacts.append(record)
    workflow.write(str(root / "workflow.yml"))
    with (root / "pegasus.properties").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(PROPERTIES)
    try:
        api_version = importlib.metadata.version("pegasus-wms.api")
    except importlib.metadata.PackageNotFoundError:
        api_version = None
    meta = {
        "record_type": "planned_run_description_not_transfer_observation",
        "generator_version": GENERATOR_VERSION, "program_version": PROGRAM_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "condition_id": condition["condition_id"], "replica": replica,
        "pattern": condition["pattern"], "mode": "CondorIO", "data_configuration": "condorio",
        "root": str(root), "active_pool": condition["active_pool"], "worker_map": worker_map,
        "tasks": condition["dag"]["tasks"], "dag": condition["dag"], "files": condition["files"],
        "file_sizes_bytes": {f["file_id"]: f["size_bytes"] for f in condition["files"]},
        "planned_requirements": validation["requirements"],
        "planned_job_id_map": {t["task_id"]: t["task_id"] for t in condition["dag"]["tasks"]},
        "resources_per_compute_task": {"request_cpus": 1, "request_memory_MiB": 256},
        "execution_site": "condorpool", "output_site": "local", "selector": "RoundRobin",
        "shared_file_system": False, "workflow_uuid": None, "actual_placements": None,
        "oracle_path": str(Path(oracle_path).resolve()), "oracle_sha256": oracle_digest,
        "input_artifacts": input_artifacts, "pegasus_api_distribution_version": api_version,
        "code_sha256": {"campaign_task.py": sha256_path(program_path),
                        "generate_workflow.py": sha256_path(Path(__file__)),
                        "fma_kernel": sha256_path(kernel_path)},
        "workflow_sha256": sha256_path(root / "workflow.yml"),
        "properties_sha256": sha256_path(root / "pegasus.properties"),
        "measurement_note": "No M_obs, DME, transfer success, or actual placement is inferred from these generated descriptions.",
    }
    with (root / "meta.json").open("x", encoding="utf-8") as stream:
        json.dump(meta, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return {"status": "prepared_not_planned_not_submitted", "condition_id": condition["condition_id"],
            "replica": replica, "root": str(root), "workflow": str(root / "workflow.yml"),
            "properties": str(root / "pegasus.properties"), "meta": str(root / "meta.json"),
            "inputs": str(root / "inputs"), "program": str(program_path),
            "oracle_sha256": oracle_digest}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--replica", required=True, type=int)
    parser.add_argument("--root", required=True, help="Exact run directory; may contain runner preflight records")
    parser.add_argument("--worker-map", required=True, help="Inline JSON object or JSON file path, optionally prefixed by @")
    parser.add_argument("--validate-only", action="store_true", help="Validate structural inputs only; no Pegasus import or file writes")
    args = parser.parse_args(argv)
    try:
        if args.replica < 1:
            raise ValueError("replica must be a positive integer")
        condition = load_condition(args.oracle, args.condition)
        worker_map = read_worker_map(args.worker_map)
        if args.validate_only:
            result = validate_condition(condition, worker_map)
        else:
            result = prepare_run(condition, args.root, worker_map, args.replica, args.oracle)
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        print(json.dumps({"status": "generation_failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
