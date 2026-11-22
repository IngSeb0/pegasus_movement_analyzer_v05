from __future__ import annotations

from dataclasses import dataclass, field

from .htcondor_source import (
    ParsedHistoryFile,
    ParsedHistoryRecord,
)
from .model import ProvenanceRef


@dataclass(slots=True)
class NormalizedHistoryIdentity:
    record_index: int

    cluster_id: int | None = None
    proc_id: int | None = None
    job_id: str | None = None

    pegasus_node_id: str | None = None
    task_id: str | None = None

    raw_remote_hosts: list[str] = field(default_factory=list)
    location_id: str | None = None

    provenance: list[ProvenanceRef] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def job_identity_resolved(self) -> bool:
        return self.job_id is not None

    @property
    def task_identity_resolved(self) -> bool:
        return self.task_id is not None

    @property
    def placement_resolved(self) -> bool:
        return self.location_id is not None


def strip_classad_quotes(raw_value: str) -> str:
    """
    Remove one matching outer pair of ClassAd double quotes.

    No other interpretation or macro expansion is performed.
    """

    value = raw_value.strip()

    if (
        len(value) >= 2
        and value.startswith('"')
        and value.endswith('"')
    ):
        return value[1:-1]

    return value


def _parse_nonnegative_integer(raw_value: str) -> int | None:
    value = strip_classad_quotes(raw_value).strip()

    if not value.isdigit():
        return None

    parsed = int(value)

    if parsed < 0:
        return None

    return parsed


def normalize_remote_host(raw_value: str) -> str | None:
    """
    Normalize an HTCondor remote-host value to a location candidate.

    Examples:
        "slot1_1@pegasus-worker2" -> pegasus-worker2
        slot1@worker.example.org  -> worker.example.org
        worker.example.org        -> worker.example.org

    This is syntactic normalization only. It does not assert that
    aliases refer to the same physical location.
    """

    value = strip_classad_quotes(raw_value).strip()

    if not value:
        return None

    if "@" in value:
        _, host = value.rsplit("@", 1)
        host = host.strip()

        if not host:
            return None

        return host.lower()

    return value.lower()


def _unique_attribute_values(
    record: ParsedHistoryRecord,
    key: str,
) -> tuple[list[str], list[ProvenanceRef]]:
    attributes = record.get_all(key)

    values = [
        attr.raw_value
        for attr in attributes
    ]

    provenance = [
        attr.provenance
        for attr in attributes
    ]

    return values, provenance


def normalize_history_identity(
    record: ParsedHistoryRecord,
) -> NormalizedHistoryIdentity:
    result = NormalizedHistoryIdentity(
        record_index=record.record_index,
    )

    # ------------------------------------------------------------------
    # HTCondor job identity: ClusterId.ProcId
    # ------------------------------------------------------------------

    cluster_values, cluster_prov = _unique_attribute_values(
        record,
        "ClusterId",
    )
    proc_values, proc_prov = _unique_attribute_values(
        record,
        "ProcId",
    )

    result.provenance.extend(cluster_prov)
    result.provenance.extend(proc_prov)

    normalized_clusters = {
        value
        for raw in cluster_values
        if (value := _parse_nonnegative_integer(raw)) is not None
    }

    normalized_procs = {
        value
        for raw in proc_values
        if (value := _parse_nonnegative_integer(raw)) is not None
    }

    if not cluster_values:
        result.issues.append("missing_cluster_id")
    elif len(normalized_clusters) != 1:
        result.issues.append("ambiguous_cluster_id")
    else:
        result.cluster_id = next(iter(normalized_clusters))

    if not proc_values:
        result.issues.append("missing_proc_id")
    elif len(normalized_procs) != 1:
        result.issues.append("ambiguous_proc_id")
    else:
        result.proc_id = next(iter(normalized_procs))

    if (
        result.cluster_id is not None
        and result.proc_id is not None
    ):
        result.job_id = (
            f"{result.cluster_id}.{result.proc_id}"
        )

    # ------------------------------------------------------------------
    # Pegasus logical task identity
    # ------------------------------------------------------------------

    node_values, node_prov = _unique_attribute_values(
        record,
        "DAGNodeName",
    )

    result.provenance.extend(node_prov)

    normalized_nodes = {
        strip_classad_quotes(raw).strip()
        for raw in node_values
        if strip_classad_quotes(raw).strip()
    }

    if not node_values:
        result.issues.append("missing_pegasus_node_id")
    elif len(normalized_nodes) != 1:
        result.issues.append("ambiguous_pegasus_node_id")
    else:
        node = next(iter(normalized_nodes))

        result.pegasus_node_id = node

        # In v1 the task identity is derived from the stable Pegasus
        # node identity, not from ClusterId or execution order.
        result.task_id = node

    # ------------------------------------------------------------------
    # Placement candidate
    # ------------------------------------------------------------------

    last_hosts, last_host_prov = _unique_attribute_values(
        record,
        "LastRemoteHost",
    )
    remote_hosts, remote_host_prov = _unique_attribute_values(
        record,
        "RemoteHost",
    )

    result.provenance.extend(last_host_prov)
    result.provenance.extend(remote_host_prov)

    result.raw_remote_hosts.extend(last_hosts)
    result.raw_remote_hosts.extend(remote_hosts)

    normalized_hosts = {
        host
        for raw in result.raw_remote_hosts
        if (host := normalize_remote_host(raw)) is not None
    }

    if not result.raw_remote_hosts:
        result.issues.append("missing_remote_host")
    elif len(normalized_hosts) != 1:
        result.issues.append("ambiguous_remote_host")
    else:
        result.location_id = next(iter(normalized_hosts))

    return result


def normalize_history_identities(
    parsed: ParsedHistoryFile,
) -> list[NormalizedHistoryIdentity]:
    return [
        normalize_history_identity(record)
        for record in parsed.records
    ]


# ---------------------------------------------------------------------------
# File identity normalization
# ---------------------------------------------------------------------------

from enum import StrEnum
from pathlib import PurePosixPath

from .pegasus_source import ParsedMetaObject


class FileIdentityMethod(StrEnum):
    EXPLICIT_LFN = "explicit_lfn"
    EXPLICIT_MAPPING = "explicit_mapping"
    PHYSICAL_PATH = "physical_path"


@dataclass(slots=True)
class NormalizedFileIdentity:
    file_id: str | None = None
    logical_name: str | None = None

    physical_paths: list[str] = field(default_factory=list)

    remap_from: str | None = None
    remap_to: str | None = None

    resolution_method: FileIdentityMethod | None = None

    provenance: list[ProvenanceRef] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.file_id is not None


def normalize_file_token(raw_value: str) -> str:
    """
    Minimal lexical normalization for an LFN/path token.

    Important:
    - surrounding whitespace is removed;
    - one outer quote pair is removed;
    - Pegasus/HTCondor macros are preserved;
    - relative paths are NOT converted to absolute paths;
    - basename is never used as identity.
    """

    return strip_classad_quotes(raw_value).strip()


def _unique_nonempty_tokens(
    values: list[str] | None,
) -> list[str]:
    if not values:
        return []

    normalized = {
        token
        for raw in values
        if (token := normalize_file_token(raw))
    }

    return sorted(normalized)


def resolve_file_identity(
    *,
    explicit_lfns: list[str] | None = None,
    mapped_lfns: list[str] | None = None,
    physical_paths: list[str] | None = None,
    remap_from: str | None = None,
    remap_to: str | None = None,
    provenance: list[ProvenanceRef] | None = None,
    physical_relation_unambiguous: bool = False,
) -> NormalizedFileIdentity:
    """
    Resolve file identity according to Design Spec precedence:

        explicit LFN
        -> explicit mapping
        -> unique physical path
        -> unresolved/ambiguous

    A physical-path fallback receives an internal `path:` prefix so it
    cannot be silently confused with an explicit logical file name.
    """

    result = NormalizedFileIdentity(
        provenance=list(provenance or []),
    )

    lfns = _unique_nonempty_tokens(explicit_lfns)
    mappings = _unique_nonempty_tokens(mapped_lfns)
    paths = _unique_nonempty_tokens(physical_paths)

    result.physical_paths = paths

    if remap_from is not None:
        result.remap_from = normalize_file_token(remap_from)

    if remap_to is not None:
        result.remap_to = normalize_file_token(remap_to)

    # ------------------------------------------------------------------
    # 1. Explicit Pegasus LFN
    # ------------------------------------------------------------------

    if len(lfns) > 1:
        result.issues.append("ambiguous_file_identity")
        return result

    if len(lfns) == 1:
        result.file_id = lfns[0]
        result.logical_name = lfns[0]
        result.resolution_method = FileIdentityMethod.EXPLICIT_LFN
        return result

    # ------------------------------------------------------------------
    # 2. Explicit mapping to an LFN
    # ------------------------------------------------------------------

    if len(mappings) > 1:
        result.issues.append("ambiguous_file_identity")
        return result

    if len(mappings) == 1:
        result.file_id = mappings[0]
        result.logical_name = mappings[0]
        result.resolution_method = FileIdentityMethod.EXPLICIT_MAPPING
        return result

    # ------------------------------------------------------------------
    # 3. Unique physical path
    # ------------------------------------------------------------------

    if len(paths) > 1:
        result.issues.append("ambiguous_file_identity")
        return result

    if len(paths) == 1:
        if physical_relation_unambiguous:
            result.file_id = f"path:{paths[0]}"
            result.resolution_method = FileIdentityMethod.PHYSICAL_PATH
            return result
        result.issues.append(
            "physical_path_not_semantically_resolved"
        )
        return result

    result.issues.append("missing_file_identity")
    return result


def normalize_meta_object_identity(
    meta_object: ParsedMetaObject,
) -> NormalizedFileIdentity:
    """
    Treat `_id` from preserved Pegasus metadata as an explicit LFN.

    This does not infer scientific role, producer, consumer, or size
    precedence.
    """

    explicit_lfns: list[str] = []

    if meta_object.object_id is not None:
        explicit_lfns.append(meta_object.object_id)

    provenance: list[ProvenanceRef] = []

    if meta_object.provenance is not None:
        provenance.append(meta_object.provenance)

    return resolve_file_identity(
        explicit_lfns=explicit_lfns,
        provenance=provenance,
    )


def file_basename_for_display(
    identity: NormalizedFileIdentity,
) -> str | None:
    """
    Convenience only.

    Basename may be displayed, but MUST NOT be used as identity.
    """

    if identity.logical_name:
        return PurePosixPath(identity.logical_name).name

    if len(identity.physical_paths) == 1:
        return PurePosixPath(identity.physical_paths[0]).name

    return None


# ---------------------------------------------------------------------------
# Documented location aliases + cross-record identity indexing
# ---------------------------------------------------------------------------

from .model import Location, LocationType


@dataclass(slots=True)
class LocationAliasRegistry:
    """
    Explicit alias registry.

    Equivalences are never inferred from string similarity.
    """

    alias_to_canonical: dict[str, str] = field(default_factory=dict)

    def register(
        self,
        canonical_id: str,
        aliases: list[str] | None = None,
    ) -> None:
        canonical = normalize_remote_host(canonical_id)

        if canonical is None:
            raise ValueError("canonical location cannot be empty")

        candidates = [canonical_id]
        candidates.extend(aliases or [])

        for raw_alias in candidates:
            alias = normalize_remote_host(raw_alias)

            if alias is None:
                raise ValueError("location alias cannot be empty")

            existing = self.alias_to_canonical.get(alias)

            if existing is not None and existing != canonical:
                raise ValueError(
                    f"location alias {alias!r} maps to both "
                    f"{existing!r} and {canonical!r}"
                )

            self.alias_to_canonical[alias] = canonical

    def resolve(self, raw_location: str) -> str | None:
        candidate = normalize_remote_host(raw_location)

        if candidate is None:
            return None

        return self.alias_to_canonical.get(
            candidate,
            candidate,
        )


def build_worker_locations(
    identities: list[NormalizedHistoryIdentity],
    alias_registry: LocationAliasRegistry | None = None,
) -> dict[str, Location]:
    """
    Build canonical worker locations from normalized history identities.

    Unknown locations remain themselves. Only explicitly registered
    aliases are collapsed into another canonical location.
    """

    registry = alias_registry or LocationAliasRegistry()

    locations: dict[str, Location] = {}

    for identity in identities:
        if identity.location_id is None:
            continue

        canonical = registry.resolve(identity.location_id)

        if canonical is None:
            continue

        location_provenance = [
            provenance
            for provenance in identity.provenance
            if provenance.attribute in {
                "lastremotehost",
                "remotehost",
            }
        ]

        if canonical not in locations:
            locations[canonical] = Location(
                location_id=canonical,
                location_type=LocationType.WORKER,
                raw_values=[],
                provenance=[],
            )

        location = locations[canonical]

        for raw_value in identity.raw_remote_hosts:
            if raw_value not in location.raw_values:
                location.raw_values.append(raw_value)

        for provenance in location_provenance:
            if provenance not in location.provenance:
                location.provenance.append(provenance)

    return locations


@dataclass(slots=True)
class IdentityRelationIndex:
    job_to_tasks: dict[str, set[str]] = field(default_factory=dict)
    task_to_jobs: dict[str, set[str]] = field(default_factory=dict)

    @property
    def conflicting_job_ids(self) -> set[str]:
        """
        Same HTCondor job claiming multiple logical Pegasus tasks.
        This is intrinsically ambiguous.
        """

        return {
            job_id
            for job_id, task_ids in self.job_to_tasks.items()
            if len(task_ids) > 1
        }

    @property
    def multi_job_task_ids(self) -> set[str]:
        """
        Logical task associated with multiple HTCondor jobs.

        This is recorded as a retry/attempt candidate. It is NOT resolved
        here because retry semantics belong to later evidence integration.
        """

        return {
            task_id
            for task_id, job_ids in self.task_to_jobs.items()
            if len(job_ids) > 1
        }


def index_identity_relations(
    identities: list[NormalizedHistoryIdentity],
) -> IdentityRelationIndex:
    index = IdentityRelationIndex()

    for identity in identities:
        if (
            identity.job_id is None
            or identity.task_id is None
        ):
            continue

        index.job_to_tasks.setdefault(
            identity.job_id,
            set(),
        ).add(identity.task_id)

        index.task_to_jobs.setdefault(
            identity.task_id,
            set(),
        ).add(identity.job_id)

    return index
