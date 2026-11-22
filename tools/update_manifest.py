"""Regenerate the portable-file inventory used by verify_snapshot.py."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reproducibility" / "MANIFEST.json"
FILES = [
    ROOT / ".gitignore",
    ROOT / ".gitattributes",
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "REPRODUCIBILIDAD.md",
    ROOT / "REPORTE_CAMBIOS.md",
    ROOT / "requirements-repro.txt",
    ROOT / "docs" / "README.md",
]
for folder in ("analysis", "data", "fixtures", "pegasus_movement", "tests", "thesis", "tools", "reproducibility"):
    FILES.extend((ROOT / folder).rglob("*"))
FILES = sorted(
    path for path in set(FILES)
    if path.is_file()
    and path != MANIFEST
    and "__pycache__" not in path.parts
    and path.suffix not in {".pyc", ".pyo"}
)


def main() -> None:
    entries = []
    for path in FILES:
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        entries.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest})
    identity = hashlib.sha256("\n".join(f"{row['path']} {row['sha256']}" for row in entries).encode()).hexdigest()
    data = {
        "format": 1,
        "scope": "Portable analyzer, tests, historical regression fixtures and processed A-H archive, free-placement validation of 7 November, current thesis source and PDF. Raw cloud capsules are archived separately.",
        "snapshot_id": identity,
        "files": entries,
    }
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Manifest regenerated: {len(entries)} files; snapshot {identity}")


if __name__ == "__main__":
    main()
