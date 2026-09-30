from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .model import ProvenanceRef, SourceKind


@dataclass(slots=True)
class HistoryAttribute:
    key: str
    raw_key: str
    raw_value: str
    line_start: int
    line_end: int
    provenance: ProvenanceRef


@dataclass(slots=True)
class ParsedHistoryRecord:
    record_index: int
    attributes: list[HistoryAttribute] = field(default_factory=list)
    structural_errors: list[str] = field(default_factory=list)

    def get_all(self, key: str) -> list[HistoryAttribute]:
        canonical = key.strip().lower()
        return [
            attr
            for attr in self.attributes
            if attr.key == canonical
        ]

    def get_last(self, key: str) -> HistoryAttribute | None:
        values = self.get_all(key)
        return values[-1] if values else None

    def value(self, key: str) -> str | None:
        attr = self.get_last(key)
        return attr.raw_value if attr else None


@dataclass(slots=True)
class ParsedHistoryFile:
    path: Path
    records: list[ParsedHistoryRecord] = field(default_factory=list)
    structural_errors: list[str] = field(default_factory=list)


def _nesting_delta(text: str) -> int:
    """
    Return bracket nesting delta outside quoted strings.

    This allows multiline nested ClassAd values such as:
        TransferInputStats = [
            Cedar = [ FilesCount = 3; TotalBytes = 100; ];
        ]
    """

    delta = 0
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True
        elif char in "[{(":
            delta += 1
        elif char in "]})":
            delta -= 1

    return delta


def parse_history_file(path: Path) -> ParsedHistoryFile:
    """
    Parse a preserved `condor_history -long` file.

    Guarantees:
    - record order is preserved;
    - attribute order is preserved;
    - unknown attributes are preserved;
    - duplicate attributes are preserved;
    - quoted values remain raw;
    - nested ClassAds remain raw;
    - source line provenance is retained.

    This function performs no job identity resolution, host normalization,
    transfer reconciliation, or scientific-byte attribution.
    """

    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"HTCondor history file does not exist: {path}"
        )

    if not path.is_file():
        raise IsADirectoryError(
            f"HTCondor history path is not a file: {path}"
        )

    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    parsed = ParsedHistoryFile(path=path)

    current_attributes: list[HistoryAttribute] = []
    current_errors: list[str] = []

    pending_key: str | None = None
    pending_raw_key: str | None = None
    pending_parts: list[str] = []
    pending_start: int | None = None
    pending_depth = 0

    def append_attribute(
        raw_key: str,
        raw_value: str,
        line_start: int,
        line_end: int,
    ) -> None:
        canonical_key = raw_key.strip().lower()

        current_attributes.append(
            HistoryAttribute(
                key=canonical_key,
                raw_key=raw_key.strip(),
                raw_value=raw_value.strip(),
                line_start=line_start,
                line_end=line_end,
                provenance=ProvenanceRef(
                    source_kind=SourceKind.HISTORY,
                    source_path=str(path),
                    attribute=canonical_key,
                    notes=(
                        f"lines {line_start}-{line_end}"
                        if line_end != line_start
                        else f"line {line_start}"
                    ),
                ),
            )
        )

    def close_record() -> None:
        nonlocal current_attributes, current_errors

        if not current_attributes and not current_errors:
            return

        parsed.records.append(
            ParsedHistoryRecord(
                record_index=len(parsed.records),
                attributes=current_attributes,
                structural_errors=current_errors,
            )
        )

        current_attributes = []
        current_errors = []

    lines = text.splitlines()

    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        if pending_key is not None:
            pending_parts.append(stripped)
            pending_depth += _nesting_delta(raw_line)

            if pending_depth <= 0:
                append_attribute(
                    pending_raw_key or pending_key,
                    " ".join(pending_parts),
                    pending_start or line_number,
                    line_number,
                )

                pending_key = None
                pending_raw_key = None
                pending_parts = []
                pending_start = None
                pending_depth = 0

            continue

        if not stripped:
            close_record()
            continue

        if "=" not in raw_line:
            current_errors.append(
                f"line {line_number}: missing '='"
            )
            continue

        raw_key, raw_value = raw_line.split("=", 1)

        raw_key = raw_key.strip()
        raw_value = raw_value.strip()

        if not raw_key:
            current_errors.append(
                f"line {line_number}: empty attribute name"
            )
            continue

        depth = _nesting_delta(raw_value)

        if depth > 0:
            pending_key = raw_key.lower()
            pending_raw_key = raw_key
            pending_parts = [raw_value]
            pending_start = line_number
            pending_depth = depth
            continue

        if depth < 0:
            current_errors.append(
                f"line {line_number}: unmatched closing bracket"
            )

        append_attribute(
            raw_key,
            raw_value,
            line_number,
            line_number,
        )

    if pending_key is not None:
        current_errors.append(
            f"line {pending_start}: unterminated nested ClassAd value"
        )

        append_attribute(
            pending_raw_key or pending_key,
            " ".join(pending_parts),
            pending_start or len(lines),
            len(lines),
        )

    close_record()

    return parsed


# ============================================================
# I8 — NORMALIZED HTCONDOR TRANSFER EVIDENCE
# ============================================================

import re as _re

from .model import (
    ProvenanceRef as _ProvenanceRef,
    SourceKind as _SourceKind,
    TransferDirection as _TransferDirection,
    TransferEvidence as _TransferEvidence,
)
from .normalize import normalize_remote_host as _normalize_remote_host


_STAT_PATTERN = _re.compile(
    r"([A-Za-z][A-Za-z0-9_]*)"
    r"(SizeBytesTotal|FilesCountTotal|"
    r"SizeBytesLastRun|FilesCountLastRun)"
    r"\s*=\s*([0-9]+)"
)


def _history_int(
    record,
    key: str,
) -> int | None:
    raw = record.value(key)

    if raw is None:
        return None

    raw = raw.strip().strip('"')

    if not _re.fullmatch(r"[0-9]+", raw):
        return None

    return int(raw)


def _history_float_as_int(
    record,
    key: str,
) -> int | None:
    raw = record.value(key)

    if raw is None:
        return None

    raw = raw.strip().strip('"')

    try:
        value = float(raw)
    except ValueError:
        return None

    if value < 0 or not value.is_integer():
        return None

    return int(value)


def _history_text(
    record,
    key: str,
) -> str | None:
    raw = record.value(key)

    if raw is None:
        return None

    raw = raw.strip()

    if (
        len(raw) >= 2
        and raw[0] == '"'
        and raw[-1] == '"'
    ):
        raw = raw[1:-1]

    return raw or None


def _job_id(record) -> str | None:
    cluster = _history_int(
        record,
        "ClusterId",
    )
    proc = _history_int(
        record,
        "ProcId",
    )

    if cluster is None or proc is None:
        return None

    return f"{cluster}.{proc}"


def _parse_transfer_stats(
    raw: str | None,
) -> tuple[
    dict[str, dict[str, int]],
    list[str],
    int | None,
    int | None,
    int | None,
    int | None,
]:
    """
    Parse protocol-specific HTCondor sandbox stats without
    discarding the original ClassAd representation.

    Supported current shape, for example:

      CedarSizeBytesTotal = ...
      CedarFilesCountTotal = ...
      CedarSizeBytesLastRun = ...
      CedarFilesCountLastRun = ...
    """

    if raw is None:
        return {}, [], None, None, None, None

    by_method: dict[
        str,
        dict[str, int],
    ] = {}

    for match in _STAT_PATTERN.finditer(raw):
        method = match.group(1)
        metric = match.group(2)
        value = int(match.group(3))

        by_method.setdefault(
            method,
            {},
        )[metric] = value

    if not by_method:
        return {}, [], None, None, None, None

    methods = sorted(by_method)

    def total(metric: str) -> int | None:
        values = [
            stats[metric]
            for stats in by_method.values()
            if metric in stats
        ]

        if len(values) != len(by_method):
            return None

        return sum(values)

    return (
        by_method,
        methods,
        total("FilesCountLastRun"),
        total("FilesCountTotal"),
        total("SizeBytesLastRun"),
        total("SizeBytesTotal"),
    )


def _stats_provenance(
    record,
    key: str,
) -> list[_ProvenanceRef]:
    attr = record.get_last(key)

    if attr is None:
        return []

    return [attr.provenance]


def _attempt_context(record) -> str | None:
    job_run_count = _history_int(
        record,
        "JobRunCount",
    )
    num_starts = _history_int(
        record,
        "NumJobStarts",
    )

    if (
        job_run_count == 1
        and num_starts == 1
    ):
        return "attempt:1"

    return None


def _direction_evidence(
    record,
    *,
    job_id: str,
    direction: _TransferDirection,
    worker_location_id: str | None,
) -> _TransferEvidence:
    if direction == _TransferDirection.INPUT:
        stats_key = "TransferInputStats"
        started_keys = (
            "TransferInStarted",
            "TransferInputStarted",
        )
        finished_keys = (
            "TransferInFinished",
            "TransferInputFinished",
        )
    else:
        stats_key = "TransferOutputStats"
        started_keys = (
            "TransferOutStarted",
            "TransferOutputStarted",
        )
        finished_keys = (
            "TransferOutFinished",
            "TransferOutputFinished",
        )

    raw_stats_value = record.value(
        stats_key
    )

    (
        parsed_stats,
        methods,
        count_last,
        count_total,
        bytes_last,
        bytes_total,
    ) = _parse_transfer_stats(
        raw_stats_value
    )

    started = None

    for key in started_keys:
        started = _history_text(
            record,
            key,
        )

        if started is not None:
            break

    finished = None

    for key in finished_keys:
        finished = _history_text(
            record,
            key,
        )

        if finished is not None:
            break

    raw_stats = {
        "transfer_stats_raw": (
            raw_stats_value
        ),
        "transfer_stats_parsed": (
            parsed_stats
        ),
        "job_status": _history_int(
            record,
            "JobStatus",
        ),
        "exit_code": _history_int(
            record,
            "ExitCode",
        ),
        "exit_by_signal": _history_text(
            record,
            "ExitBySignal",
        ),
        "job_run_count": _history_int(
            record,
            "JobRunCount",
        ),
        "num_job_starts": _history_int(
            record,
            "NumJobStarts",
        ),
        "num_shadow_starts": _history_int(
            record,
            "NumShadowStarts",
        ),
        "hold_reason": _history_text(
            record,
            "HoldReason",
        ),
    }

    provenance = []

    provenance.extend(
        _stats_provenance(
            record,
            stats_key,
        )
    )

    for key in (
        "ClusterId",
        "ProcId",
        "LastRemoteHost",
        "RemoteHost",
        "JobRunCount",
        "NumJobStarts",
        "JobStatus",
        "ExitCode",
        "BytesRecvd",
        "BytesSent",
    ):
        attr = record.get_last(key)

        if attr is not None:
            provenance.append(
                attr.provenance
            )

    return _TransferEvidence(
        job_id=job_id,
        direction=direction,
        attempt_context=(
            _attempt_context(record)
        ),
        worker_location_id=(
            worker_location_id
        ),
        raw_stats=raw_stats,
        methods=methods,
        observed_file_count_last=(
            count_last
        ),
        observed_file_count_total=(
            count_total
        ),
        observed_bytes_last=(
            bytes_last
        ),
        observed_bytes_total=(
            bytes_total
        ),
        bytes_recvd=(
            _history_float_as_int(
                record,
                "BytesRecvd",
            )
        ),
        bytes_sent=(
            _history_float_as_int(
                record,
                "BytesSent",
            )
        ),
        transfer_started=started,
        transfer_finished=finished,
        provenance=provenance,
    )


def build_transfer_evidence(
    parsed_history: ParsedHistoryFile,
    *,
    scientific_job_ids: set[str],
) -> list[_TransferEvidence]:
    """
    Normalize HTCondor transfer evidence only for scientific
    jobs already identified by the integrated execution model.

    The complete history may contain unrelated Pegasus runs, so
    filtering by known job_id is mandatory.
    """

    evidence: list[
        _TransferEvidence
    ] = []

    for record in parsed_history.records:
        job_id = _job_id(record)

        if (
            job_id is None
            or job_id
            not in scientific_job_ids
        ):
            continue

        remote_host = (
            _history_text(
                record,
                "LastRemoteHost",
            )
            or _history_text(
                record,
                "RemoteHost",
            )
        )

        worker = (
            _normalize_remote_host(
                remote_host
            )
            if remote_host is not None
            else None
        )

        evidence.append(
            _direction_evidence(
                record,
                job_id=job_id,
                direction=(
                    _TransferDirection.INPUT
                ),
                worker_location_id=worker,
            )
        )

        evidence.append(
            _direction_evidence(
                record,
                job_id=job_id,
                direction=(
                    _TransferDirection.OUTPUT
                ),
                worker_location_id=worker,
            )
        )

    return evidence
