from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RawRunSources:
    """
    Raw files discovered inside one Pegasus run directory.

    This object only records source locations. It does not interpret
    workflow semantics, classify scientific files, or calculate metrics.
    """

    run_path: Path

    submit_files: list[Path] = field(default_factory=list)
    meta_files: list[Path] = field(default_factory=list)
    cache_meta_files: list[Path] = field(default_factory=list)
    dag_files: list[Path] = field(default_factory=list)
    braindump_files: list[Path] = field(default_factory=list)
    config_files: list[Path] = field(default_factory=list)
    event_log_files: list[Path] = field(default_factory=list)


def _sorted_unique(paths) -> list[Path]:
    return sorted(
        {p.resolve() for p in paths if p.is_file()},
        key=lambda p: str(p),
    )


def load_run_sources(run_path: Path) -> RawRunSources:
    """
    Discover raw Pegasus artifacts without modifying the run.

    All returned paths are absolute and deterministic.
    """

    run_path = Path(run_path).expanduser().resolve()

    if not run_path.exists():
        raise FileNotFoundError(f"Run directory does not exist: {run_path}")

    if not run_path.is_dir():
        raise NotADirectoryError(f"Run path is not a directory: {run_path}")

    all_meta = _sorted_unique(run_path.rglob("*.meta"))

    cache_meta = [
        p for p in all_meta
        if p.name == "cache.meta" or p.name.endswith(".cache.meta")
    ]

    normal_meta = [
        p for p in all_meta
        if p not in set(cache_meta)
    ]

    braindump = _sorted_unique(
        list(run_path.rglob("braindump.txt"))
        + list(run_path.rglob("braindump.yml"))
        + list(run_path.rglob("braindump.yaml"))
        + list(run_path.rglob("braindump.json"))
    )

    config = _sorted_unique(
        list(run_path.rglob("pegasus.properties"))
        + list(run_path.rglob("*.properties"))
    )

    return RawRunSources(
        run_path=run_path,
        submit_files=_sorted_unique(run_path.rglob("*.sub")),
        meta_files=normal_meta,
        cache_meta_files=cache_meta,
        dag_files=_sorted_unique(run_path.rglob("*.dag")),
        braindump_files=braindump,
        config_files=config,
        event_log_files=_sorted_unique(run_path.rglob("*.log")),
    )


# ---------------------------------------------------------------------------
# Condor submit-file parsing
# ---------------------------------------------------------------------------

from .model import ProvenanceRef, SourceKind


@dataclass(slots=True)
class SubmitAttribute:
    key: str
    raw_key: str
    raw_value: str
    line_number: int
    provenance: ProvenanceRef


@dataclass(slots=True)
class SubmitDirective:
    text: str
    line_number: int
    provenance: ProvenanceRef


@dataclass(slots=True)
class ParsedSubmitFile:
    path: Path
    attributes: list[SubmitAttribute] = field(default_factory=list)
    directives: list[SubmitDirective] = field(default_factory=list)

    def get_all(self, key: str) -> list[SubmitAttribute]:
        canonical = key.strip().lower()
        return [
            attr
            for attr in self.attributes
            if attr.key == canonical
        ]

    def get_last(self, key: str) -> SubmitAttribute | None:
        values = self.get_all(key)
        return values[-1] if values else None

    def value(self, key: str) -> str | None:
        attr = self.get_last(key)
        return attr.raw_value if attr else None


def _logical_submit_lines(text: str) -> list[tuple[int, str]]:
    """
    Join simple HTCondor backslash continuations while preserving the
    starting physical line number for provenance.
    """

    result: list[tuple[int, str]] = []
    buffer: list[str] = []
    start_line: int | None = None

    for line_number, raw in enumerate(text.splitlines(), start=1):
        stripped_right = raw.rstrip()

        if start_line is None:
            start_line = line_number

        if stripped_right.endswith("\\"):
            buffer.append(stripped_right[:-1].strip())
            continue

        buffer.append(stripped_right.strip())
        logical = " ".join(part for part in buffer if part)

        result.append((start_line, logical))

        buffer = []
        start_line = None

    if buffer:
        result.append(
            (
                start_line if start_line is not None else 1,
                " ".join(part for part in buffer if part),
            )
        )

    return result


def parse_submit_file(path: Path) -> ParsedSubmitFile:
    """
    Parse one HTCondor submit file without applying workflow semantics.

    Important:
    - raw values are preserved;
    - paths/macros are NOT reduced to basenames;
    - duplicate attributes are preserved in source order;
    - non-assignment directives such as `queue` are preserved;
    - every parsed element carries source provenance.
    """

    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Submit file does not exist: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"Submit path is not a file: {path}")

    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    parsed = ParsedSubmitFile(path=path)

    for line_number, logical_line in _logical_submit_lines(text):
        line = logical_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        provenance = ProvenanceRef(
            source_kind=SourceKind.SUBMIT,
            source_path=str(path),
            notes=f"line {line_number}",
        )

        if "=" not in line:
            parsed.directives.append(
                SubmitDirective(
                    text=line,
                    line_number=line_number,
                    provenance=provenance,
                )
            )
            continue

        raw_key, raw_value = line.split("=", 1)

        raw_key = raw_key.strip()
        raw_value = raw_value.strip()

        if not raw_key:
            continue

        canonical_key = raw_key.lower()

        parsed.attributes.append(
            SubmitAttribute(
                key=canonical_key,
                raw_key=raw_key,
                raw_value=raw_value,
                line_number=line_number,
                provenance=ProvenanceRef(
                    source_kind=SourceKind.SUBMIT,
                    source_path=str(path),
                    attribute=canonical_key,
                    notes=f"line {line_number}",
                ),
            )
        )

    return parsed


def parse_submit_files(
    paths: list[Path],
) -> list[ParsedSubmitFile]:
    return [
        parse_submit_file(path)
        for path in sorted(paths, key=lambda p: str(p))
    ]


# ---------------------------------------------------------------------------
# Pegasus .meta / cache.meta JSON parsing
# ---------------------------------------------------------------------------

import json
import re
from typing import Any


@dataclass(slots=True)
class ParsedMetaObject:
    object_index: int
    object_id: str | None
    attributes: dict[str, Any]
    raw_object: dict[str, Any]

    raw_size: Any = None
    size_bytes: int | None = None
    size_error: str | None = None

    provenance: ProvenanceRef | None = None
    size_provenance: ProvenanceRef | None = None


@dataclass(slots=True)
class ParsedMetaFile:
    path: Path
    raw_document: Any = None
    objects: list[ParsedMetaObject] = field(default_factory=list)

    parse_error: str | None = None
    structural_errors: list[str] = field(default_factory=list)

    provenance: ProvenanceRef | None = None

    @property
    def is_cache_meta(self) -> bool:
        return (
            self.path.name == "cache.meta"
            or self.path.name.endswith(".cache.meta")
        )


def _parse_nonnegative_integer(value: Any) -> tuple[int | None, str | None]:
    """
    Strict parser for byte counts.

    We preserve invalid raw values instead of coercing them silently.
    """

    if value is None:
        return None, None

    if isinstance(value, bool):
        return None, "boolean_is_not_a_valid_size"

    if isinstance(value, int):
        if value < 0:
            return None, "negative_size"
        return value, None

    if isinstance(value, str):
        text = value.strip()

        if not text:
            return None, "empty_size"

        if not re.fullmatch(r"[+-]?\d+", text):
            return None, "size_is_not_an_integer"

        parsed = int(text)

        if parsed < 0:
            return None, "negative_size"

        return parsed, None

    return None, f"unsupported_size_type:{type(value).__name__}"


def parse_meta_file(path: Path) -> ParsedMetaFile:
    """
    Parse one Pegasus .meta/cache.meta JSON document.

    This function preserves the original parsed JSON and provenance.
    It does NOT resolve file identity conflicts and does NOT decide
    whether a file is scientific.
    """

    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Metadata file does not exist: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"Metadata path is not a file: {path}")

    file_provenance = ProvenanceRef(
        source_kind=SourceKind.META,
        source_path=str(path),
        notes="cache_meta" if (
            path.name == "cache.meta"
            or path.name.endswith(".cache.meta")
        ) else "meta",
    )

    parsed = ParsedMetaFile(
        path=path,
        provenance=file_provenance,
    )

    raw_text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    try:
        document = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        parsed.parse_error = (
            f"JSONDecodeError line={exc.lineno} "
            f"column={exc.colno}: {exc.msg}"
        )
        return parsed

    parsed.raw_document = document

    if isinstance(document, dict):
        raw_objects: list[Any] = [document]
    elif isinstance(document, list):
        raw_objects = document
    else:
        parsed.structural_errors.append(
            "top_level_json_must_be_object_or_array"
        )
        return parsed

    for index, raw_object in enumerate(raw_objects):
        if not isinstance(raw_object, dict):
            parsed.structural_errors.append(
                f"object[{index}]_is_{type(raw_object).__name__}_not_object"
            )
            continue

        raw_id = raw_object.get("_id")
        object_id = None if raw_id is None else str(raw_id)

        raw_attributes = raw_object.get("_attributes")

        if raw_attributes is None:
            attributes: dict[str, Any] = {}
        elif isinstance(raw_attributes, dict):
            attributes = dict(raw_attributes)
        else:
            attributes = {}
            parsed.structural_errors.append(
                f"object[{index}]._attributes_is_"
                f"{type(raw_attributes).__name__}_not_object"
            )

        raw_size = attributes.get("size")
        size_bytes, size_error = _parse_nonnegative_integer(raw_size)

        object_provenance = ProvenanceRef(
            source_kind=SourceKind.META,
            source_path=str(path),
            notes=f"object_index={index}",
        )

        size_provenance = None

        if "size" in attributes:
            size_provenance = ProvenanceRef(
                source_kind=SourceKind.META,
                source_path=str(path),
                attribute="_attributes.size",
                notes=(
                    f"object_index={index}; "
                    f"object_id={object_id!r}"
                ),
            )

        parsed.objects.append(
            ParsedMetaObject(
                object_index=index,
                object_id=object_id,
                attributes=attributes,
                raw_object=dict(raw_object),
                raw_size=raw_size,
                size_bytes=size_bytes,
                size_error=size_error,
                provenance=object_provenance,
                size_provenance=size_provenance,
            )
        )

    return parsed


def parse_meta_files(
    paths: list[Path],
) -> list[ParsedMetaFile]:
    return [
        parse_meta_file(path)
        for path in sorted(paths, key=lambda p: str(p))
    ]
