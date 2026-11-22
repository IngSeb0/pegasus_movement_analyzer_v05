"""Correspondencia científica entre tareas y jobs desde fuentes nativas.

No ejecuta comandos del plan y no considera una planificación como ejecución.
Solo admite el formato secuencial pegasus-cluster con anotaciones y -N coherentes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
import shlex

import yaml

from .diagnostics import AnalysisStatus, Diagnostic, ReasonCode
from .model import ProvenanceRef, SourceKind
from .pegasus_source import ParsedSubmitFile


@dataclass(slots=True)
class TaskJobMapping:
    task_to_node: dict[str, str] = field(default_factory=dict)
    node_members: dict[str, list[str]] = field(default_factory=dict)
    provenance: list[ProvenanceRef] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return bool(self.task_to_node) and not self.diagnostics

    @property
    def grouped(self) -> bool:
        return any(len(members) > 1 for members in self.node_members.values())


def _scalar(submit: ParsedSubmitFile, key: str) -> str | None:
    values = {a.raw_value.strip().strip('"').strip() for a in submit.get_all(key)}
    if len(values) != 1:
        return None
    return next(iter(values))


def _sequential_members(path: Path) -> list[str]:
    annotations: list[str] = []
    commands: list[str] = []
    pending: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#@"):
            m = re.fullmatch(r"#@\s+(\d+)\s+\S+\s+(\S+)\s*", line)
            if not m or pending is not None or int(m[1]) != len(annotations) + 1:
                raise ValueError("Anotación de agrupación ausente, duplicada o fuera de orden")
            pending = m[2]
            annotations.append(pending)
            continue
        if line.startswith("#"):
            continue
        tokens = shlex.split(line, posix=True)
        if not tokens or Path(tokens[0]).name != "pegasus-kickstart":
            raise ValueError("El grupo contiene una instrucción fuera del formato admitido")
        if tokens.count("-N") != 1:
            raise ValueError("Identidad -N ausente o ambigua")
        i = tokens.index("-N")
        if i + 1 >= len(tokens) or tokens[i + 1] != pending:
            raise ValueError("La anotación no coincide con la invocación de la tarea")
        commands.append(tokens[i + 1])
        pending = None
    if pending is not None or annotations != commands or len(commands) != len(set(commands)):
        raise ValueError("Pertenencia o instrucciones incompletas del grupo")
    return commands


def resolve_task_job_mapping(workflow_path: str | Path, submits) -> TaskJobMapping:
    result = TaskJobMapping()
    workflow_path = Path(workflow_path)

    def reject(message, source, *, missing=False):
        result.diagnostics.append(Diagnostic(
            status=AnalysisStatus.INCOMPLETE_EVIDENCE if missing else AnalysisStatus.INCONSISTENT,
            reason_code=ReasonCode.AMBIGUOUS_JOB_IDENTITY,
            message=message, context={"source": str(source)}, provenance=[]))

    if not workflow_path.is_file():
        reject("Falta el workflow científico para verificar los miembros", workflow_path, missing=True)
        return result
    try:
        raw = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("jobs"), list):
            raise ValueError("Workflow sin lista científica de tareas")
        if any(not isinstance(j, dict) for j in raw["jobs"]):
            raise ValueError("Registro de tarea inválido")
        jobs = [j for j in raw["jobs"] if str(j.get("type", "job")).lower() == "job"]
        ids = [j["id"] for j in jobs]
        if not ids or any(not isinstance(t, str) or not t for t in ids) or len(ids) != len(set(ids)):
            raise ValueError("Identidades científicas ausentes o duplicadas")
    except (KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        reject(str(error), workflow_path)
        return result
    scientific_ids = set(ids)
    producers: dict[str, str] = {}
    edges: set[tuple[str, str]] = set()
    for j in jobs:
        uses = j.get("uses", [])
        if not isinstance(uses, list) or any(not isinstance(u, dict) or not isinstance(u.get("lfn"), str) for u in uses):
            reject("Usos de archivo mal definidos", workflow_path)
            return result
        for use in j.get("uses", []):
            if use.get("type") == "output":
                lfn = use.get("lfn")
                if lfn in producers and producers[lfn] != j["id"]:
                    reject("Un archivo tiene varios productores", workflow_path)
                producers[lfn] = j["id"]
    for j in jobs:
        for use in j.get("uses", []):
            if use.get("type") == "input" and use.get("lfn") in producers:
                edges.add((producers[use["lfn"]], j["id"]))
    dependencies = raw.get("jobDependencies", [])
    if not isinstance(dependencies, list):
        reject("Dependencias explícitas mal definidas", workflow_path)
        return result
    for dep in dependencies:
        if not isinstance(dep, dict) or dep.get("id") not in scientific_ids or not isinstance(dep.get("children"), list):
            reject("Dependencia explícita sin identidad válida", workflow_path)
            return result
        for child in dep["children"]:
            if child not in scientific_ids:
                reject("Dependencia explícita con tarea desconocida", workflow_path)
            else:
                edges.add((dep["id"], child))
    for submit in submits:
        if _scalar(submit, "+pegasus_job_class") != "1":
            continue
        node = _scalar(submit, "+pegasus_wf_dag_job_id")
        dax = _scalar(submit, "+pegasus_wf_dax_job_id")
        size = _scalar(submit, "+pegasus_cluster_size")
        if not node or node in result.node_members:
            reject("Nodo ejecutable ausente o repetido", submit.path)
            continue
        try:
            if dax is not None and dax.lower() not in {"null", "undefined", ""}:
                if size is not None and size != "1":
                    raise ValueError("Submit individual con tamaño de grupo contradictorio")
                members = [dax]
            else:
                if _scalar(submit, "+pegasus_wf_xformation") != "pegasus::seqexec":
                    raise ValueError("El submit agrupado no demuestra pegasus::seqexec")
                if size is None or not size.isdecimal() or int(size) < 2:
                    raise ValueError("Tamaño de grupo ausente o inválido")
                native = submit.path.with_suffix(".in")
                if not native.is_file():
                    reject("Falta la lista nativa de tareas agrupadas", native, missing=True)
                    continue
                members = _sequential_members(native)
                if len(members) != int(size):
                    raise ValueError("Los miembros no coinciden con pegasus_cluster_size")
                result.provenance.append(ProvenanceRef(
                    source_kind=SourceKind.SUBMIT, source_path=str(native),
                    source_hash=hashlib.sha256(native.read_bytes()).hexdigest(),
                    notes="Miembros y orden del plan; no prueba ejecución individual"))
            if any(t not in scientific_ids or t in result.task_to_node for t in members):
                raise ValueError("Tarea desconocida o presente en más de un job")
            order = {t: i for i, t in enumerate(members)}
            if any(a in order and b in order and order[a] >= order[b] for a, b in edges):
                raise ValueError("Orden del grupo incompatible con el DAG científico")
            if node in scientific_ids and members != [node]:
                raise ValueError("Colisión entre identidad de tarea y nodo ejecutable")
            result.node_members[node] = members
            result.task_to_node.update((t, node) for t in members)
            result.provenance.extend(a.provenance for a in submit.get_all("+pegasus_wf_dag_job_id"))
        except (ValueError, OSError) as error:
            reject(str(error), submit.path)
    if set(result.task_to_node) != scientific_ids:
        reject("La correspondencia no cubre exactamente las tareas científicas", workflow_path)
    if result.diagnostics:
        # No se permite consumir una correspondencia parcialmente válida.
        result.task_to_node.clear()
        result.node_members.clear()
    return result
