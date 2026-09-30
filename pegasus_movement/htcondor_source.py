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
