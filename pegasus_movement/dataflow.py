from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import yaml

from .diagnostics import (
    AnalysisStatus,
    Diagnostic,
    ReasonCode,
)
from .execution_model import is_pegasus_compute_submit
from .model import (
    FileRole,
    ProvenanceRef,
    ScientificFile,
    SourceKind,
)
from .normalize import strip_classad_quotes
from .pegasus_source import ParsedSubmitFile


@dataclass(slots=True)
class DataflowBuildResult:
    scientific_files: dict[str, ScientificFile] = field(
        default_factory=dict
    )
    task_ids: list[str] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(
        default_factory=list
    )


@dataclass(slots=True)
class _FileDraft:
    logical_name: str
    producers: set[str] = field(default_factory=set)
    consumers: set[str] = field(default_factory=set)
    replica_sites: set[str] = field(default_factory=set)
    physical_refs: set[str] = field(default_factory=set)
    declared_output: bool = False
    stage_out: bool = False


def _provenance(
    path: Path,
    attribute: str | None = None,
    notes: str | None = None,
) -> ProvenanceRef:
    return ProvenanceRef(
        source_kind=SourceKind.CONFIG,
        source_path=str(path),
        attribute=attribute,
        notes=notes,
    )


def _diagnostic(
    status: AnalysisStatus,
    reason: ReasonCode,
    message: str,
    *,
    context: dict | None = None,
    provenance: list[ProvenanceRef] | None = None,
) -> Diagnostic:
    return Diagnostic(
        status=status,
        reason_code=reason,
        message=message,
        context=context or {},
        provenance=provenance or [],
    )


def lfn_file_id(logical_name: str) -> str:
    """
    Stable explicit-Pegasus-LFN identity.

    This intentionally does not derive identity from basename or
    physical location.
    """

    return f"lfn:{logical_name}"


def _clean_submit_value(
    submit: ParsedSubmitFile,
    key: str,
) -> str | None:
    raw = submit.value(key)

    if raw is None:
        return None

    value = strip_classad_quotes(raw)

    if value is None:
        return None

    value = value.strip()

    return value or None


def _build_dax_to_task_id(
    submits: Iterable[ParsedSubmitFile],
) -> tuple[dict[str, str], list[Diagnostic]]:
    candidates: dict[str, set[str]] = {}
    diagnostics: list[Diagnostic] = []

    for submit in submits:
        if not is_pegasus_compute_submit(submit):
            continue

        dax_id = _clean_submit_value(
            submit,
            "+pegasus_wf_dax_job_id",
        )
        dag_id = _clean_submit_value(
            submit,
            "+pegasus_wf_dag_job_id",
        )

        if dax_id is None or dag_id is None:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.AMBIGUOUS_JOB_IDENTITY,
                    (
                        "Compute submit lacks an unambiguous "
                        "Pegasus DAX/DAG identity."
                    ),
                    context={
                        "submit": str(submit.path),
                        "dax_id": dax_id,
                        "dag_id": dag_id,
                    },
                )
            )
            continue

        candidates.setdefault(
            dax_id,
            set(),
        ).add(dag_id)

    resolved: dict[str, str] = {}

    for dax_id, task_ids in candidates.items():
        if len(task_ids) != 1:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.AMBIGUOUS_JOB_IDENTITY,
                    (
                        "One Pegasus workflow job maps to "
                        "multiple logical task identities."
                    ),
                    context={
                        "dax_id": dax_id,
                        "task_ids": sorted(task_ids),
                    },
                )
            )
            continue

        resolved[dax_id] = next(iter(task_ids))

    return resolved, diagnostics


def _walk_dicts(value):
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from _walk_dicts(child)

    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _strict_nonnegative_int(
    value,
) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value >= 0 else None

    if isinstance(value, str):
        stripped = value.strip()

        if re.fullmatch(r"[0-9]+", stripped):
            return int(stripped)

    return None


def _collect_size_values(value) -> list[int]:
    result: list[int] = []

    if isinstance(value, dict):
        key_value = (
            value.get("_key")
            if "_key" in value
            else value.get("key")
        )

        if (
            isinstance(key_value, str)
            and key_value.strip().lower() == "size"
        ):
            for candidate_key in (
                "_value",
                "value",
                "size",
            ):
                if candidate_key in value:
                    parsed = _strict_nonnegative_int(
                        value[candidate_key]
                    )

                    if parsed is not None:
                        result.append(parsed)

        for key, child in value.items():
            if str(key).strip().lower() == "size":
                parsed = _strict_nonnegative_int(child)

                if parsed is not None:
                    result.append(parsed)

            if key not in {
                "_key",
                "key",
                "_value",
                "value",
                "size",
            }:
                result.extend(
                    _collect_size_values(child)
                )

    elif isinstance(value, list):
        for child in value:
            result.extend(
                _collect_size_values(child)
            )

    return result


def _meta_sizes_for_lfn(
    logical_name: str,
    meta_paths: Iterable[Path],
) -> tuple[
    set[int],
    list[ProvenanceRef],
]:
    sizes: set[int] = set()
    provenance: list[ProvenanceRef] = []

    for path in meta_paths:
        path = Path(path)

        if not path.exists():
            continue

        try:
            raw = json.loads(
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )
        except (OSError, json.JSONDecodeError):
            continue

        for record in _walk_dicts(raw):
            record_id = record.get("_id")

            if record_id is None:
                record_id = record.get("id")

            if str(record_id) != logical_name:
                continue

            attributes = record.get(
                "_attributes",
                record.get("attributes", {}),
            )

            found = _collect_size_values(
                attributes
            )

            for size in found:
                sizes.add(size)

            if found:
                provenance.append(
                    ProvenanceRef(
                        source_kind=SourceKind.META,
                        source_path=str(path),
                        attribute=f"{logical_name}:size",
                        notes=(
                            "Pegasus metadata linked by "
                            "explicit logical file identity"
                        ),
                    )
                )

    return sizes, provenance


def _physical_path_from_ref(
    raw_ref: str,
) -> Path | None:
    parsed = urlparse(raw_ref)

    if parsed.scheme == "file":
        return Path(parsed.path)

    if parsed.scheme:
        return None

    return Path(raw_ref)


def _physical_sizes(
    physical_refs: Iterable[str],
) -> tuple[
    set[int],
    list[ProvenanceRef],
]:
    sizes: set[int] = set()
    provenance: list[ProvenanceRef] = []

    for raw in physical_refs:
        path = _physical_path_from_ref(raw)

        if (
            path is None
            or not path.exists()
            or not path.is_file()
        ):
            continue

        sizes.add(path.stat().st_size)

        provenance.append(
            ProvenanceRef(
                source_kind=SourceKind.PHYSICAL_FILE,
                source_path=str(path),
                attribute="st_size",
                notes=(
                    "Physical file is linked to the LFN "
                    "by preserved workflow semantics"
                ),
            )
        )

    return sizes, provenance


def _resolve_size(
    logical_name: str,
    physical_refs: Iterable[str],
    meta_paths: Iterable[Path],
) -> tuple[
    int | None,
    list[ProvenanceRef],
    ReasonCode | None,
]:
    meta_sizes, meta_provenance = (
        _meta_sizes_for_lfn(
            logical_name,
            meta_paths,
        )
    )

    if len(meta_sizes) > 1:
        return (
            None,
            meta_provenance,
            ReasonCode.CONFLICTING_FILE_SIZE,
        )

    if len(meta_sizes) == 1:
        return (
            next(iter(meta_sizes)),
            meta_provenance,
            None,
        )

    physical_sizes, physical_provenance = (
        _physical_sizes(physical_refs)
    )

    if len(physical_sizes) > 1:
        return (
            None,
            physical_provenance,
            ReasonCode.CONFLICTING_FILE_SIZE,
        )

    if len(physical_sizes) == 1:
        return (
            next(iter(physical_sizes)),
            physical_provenance,
            None,
        )

    return (
        None,
        [],
        ReasonCode.MISSING_FILE_SIZE,
    )


def build_scientific_dataflow(
    workflow_path: str | Path,
    *,
    submits: Iterable[ParsedSubmitFile],
    site_location_map: dict[str, str],
    final_destination_location_id: str | None,
    meta_paths: Iterable[str | Path] = (),
) -> DataflowBuildResult:
    """
    Reconstruct the logical scientific dataflow from Pegasus semantics.

    Pattern names and placement labels are deliberately ignored.
    """

    workflow_path = Path(
        workflow_path
    ).expanduser().resolve()

    raw = yaml.safe_load(
        workflow_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(raw, dict):
        raise ValueError(
            "workflow.yml must contain a mapping"
        )

    submit_list = list(submits)

    dax_to_task_id, diagnostics = (
        _build_dax_to_task_id(submit_list)
    )

    drafts: dict[str, _FileDraft] = {}

    def draft_for(lfn: str) -> _FileDraft:
        return drafts.setdefault(
            lfn,
            _FileDraft(logical_name=lfn),
        )

    replica_catalog = raw.get(
        "replicaCatalog",
        {},
    ) or {}

    replicas = replica_catalog.get(
        "replicas",
        [],
    ) or []

    for replica in replicas:
        if not isinstance(replica, dict):
            continue

        lfn = replica.get("lfn")

        if not isinstance(lfn, str):
            continue

        draft = draft_for(lfn)

        for pfn_record in (
            replica.get("pfns", []) or []
        ):
            if not isinstance(
                pfn_record,
                dict,
            ):
                continue

            site = pfn_record.get("site")
            pfn = pfn_record.get("pfn")

            if isinstance(site, str):
                draft.replica_sites.add(site)

            if isinstance(pfn, str):
                draft.physical_refs.add(pfn)

    task_ids: set[str] = set()

    for job in raw.get("jobs", []) or []:
        if not isinstance(job, dict):
            continue

        if str(
            job.get("type", "job")
        ).lower() != "job":
            continue

        dax_id = job.get("id")

        if not isinstance(dax_id, str):
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.AMBIGUOUS_JOB_IDENTITY,
                    (
                        "Scientific workflow job has no "
                        "stable Pegasus id."
                    ),
                    context={"job": job},
                    provenance=[
                        _provenance(
                            workflow_path,
                            "jobs[].id",
                        )
                    ],
                )
            )
            continue

        task_id = dax_to_task_id.get(dax_id)

        if task_id is None:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.AMBIGUOUS_JOB_IDENTITY,
                    (
                        "Pegasus workflow job cannot be "
                        "mapped to exactly one compute submit."
                    ),
                    context={"dax_id": dax_id},
                    provenance=[
                        _provenance(
                            workflow_path,
                            "jobs[].id",
                        )
                    ],
                )
            )
            continue

        task_ids.add(task_id)

        for use in job.get("uses", []) or []:
            if not isinstance(use, dict):
                continue

            lfn = use.get("lfn")
            use_type = use.get("type")

            if (
                not isinstance(lfn, str)
                or not isinstance(
                    use_type,
                    str,
                )
            ):
                continue

            draft = draft_for(lfn)

            if use_type.lower() == "input":
                draft.consumers.add(task_id)

            elif use_type.lower() == "output":
                draft.producers.add(task_id)
                draft.declared_output = True

                if bool(
                    use.get("stageOut", False)
                ):
                    draft.stage_out = True

    meta_path_list = [
        Path(path)
        for path in meta_paths
    ]

    scientific_files: dict[
        str,
        ScientificFile,
    ] = {}

    for logical_name, draft in sorted(
        drafts.items()
    ):
        roles: set[FileRole] = set()

        if (
            not draft.producers
            and draft.consumers
        ):
            roles.add(
                FileRole.EXTERNAL_INPUT
            )

        if (
            draft.producers
            and draft.consumers
        ):
            roles.add(
                FileRole.INTERMEDIATE
            )

        if (
            draft.stage_out
            or (
                draft.declared_output
                and not draft.consumers
            )
        ):
            roles.add(
                FileRole.FINAL_OUTPUT
            )

        if not roles:
            continue

        producer_task_id: str | None

        if len(draft.producers) > 1:
            producer_task_id = None

            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.MULTIPLE_PRODUCERS,
                    (
                        "Scientific LFN has multiple "
                        "unversioned producers."
                    ),
                    context={
                        "logical_name": logical_name,
                        "producers": sorted(
                            draft.producers
                        ),
                    },
                    provenance=[
                        _provenance(
                            workflow_path,
                            f"lfn:{logical_name}",
                        )
                    ],
                )
            )

        elif len(draft.producers) == 1:
            producer_task_id = next(
                iter(draft.producers)
            )

        else:
            producer_task_id = None

        origin_location_id = None

        if FileRole.EXTERNAL_INPUT in roles:
            mapped_origins = {
                site_location_map[site]
                for site in draft.replica_sites
                if site in site_location_map
            }

            if len(mapped_origins) == 1:
                origin_location_id = next(
                    iter(mapped_origins)
                )

            elif len(mapped_origins) != 1:
                diagnostics.append(
                    _diagnostic(
                        AnalysisStatus.INCOMPLETE_EVIDENCE,
                        ReasonCode.MISSING_PLACEMENT,
                        (
                            "External scientific input "
                            "has no unique declared origin."
                        ),
                        context={
                            "logical_name": logical_name,
                            "replica_sites": sorted(
                                draft.replica_sites
                            ),
                            "mapped_origins": sorted(
                                mapped_origins
                            ),
                        },
                    )
                )

        final_destinations: list[str] = []

        if FileRole.FINAL_OUTPUT in roles:
            if final_destination_location_id:
                final_destinations = [
                    final_destination_location_id
                ]

            else:
                diagnostics.append(
                    _diagnostic(
                        AnalysisStatus.INCOMPLETE_EVIDENCE,
                        ReasonCode.MISSING_PLACEMENT,
                        (
                            "Final scientific output "
                            "has no declared final location."
                        ),
                        context={
                            "logical_name": logical_name,
                        },
                    )
                )

        size_bytes, size_provenance, size_issue = (
            _resolve_size(
                logical_name,
                draft.physical_refs,
                meta_path_list,
            )
        )

        if size_issue is not None:
            diagnostics.append(
                _diagnostic(
                    (
                        AnalysisStatus.INCONSISTENT
                        if size_issue
                        == ReasonCode.CONFLICTING_FILE_SIZE
                        else
                        AnalysisStatus.INCOMPLETE_EVIDENCE
                    ),
                    size_issue,
                    (
                        "Scientific file size could not "
                        "be resolved authoritatively."
                    ),
                    context={
                        "logical_name": logical_name,
                        "physical_refs": sorted(
                            draft.physical_refs
                        ),
                    },
                    provenance=size_provenance,
                )
            )

        file_id = lfn_file_id(
            logical_name
        )

        scientific_files[file_id] = (
            ScientificFile(
                file_id=file_id,
                logical_name=logical_name,
                physical_refs=sorted(
                    draft.physical_refs
                ),
                roles=roles,
                size_bytes=size_bytes,
                size_provenance=size_provenance,
                producer_task_id=producer_task_id,
                consumer_task_ids=sorted(
                    draft.consumers
                ),
                origin_location_id=(
                    origin_location_id
                ),
                final_destination_ids=(
                    final_destinations
                ),
                identity_provenance=[
                    _provenance(
                        workflow_path,
                        f"lfn:{logical_name}",
                        notes=(
                            "Explicit Pegasus logical "
                            "file identity"
                        ),
                    )
                ],
            )
        )

    return DataflowBuildResult(
        scientific_files=scientific_files,
        task_ids=sorted(task_ids),
        diagnostics=diagnostics,
    )
