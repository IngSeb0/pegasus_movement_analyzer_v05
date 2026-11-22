"""Check the documented code/fixture snapshot without network or cloud access."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    manifest = ROOT / "reproducibility" / "MANIFEST.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    failures = []
    for entry in data["files"]:
        relative = Path(entry["path"])
        path = (ROOT / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(ROOT):
            failures.append(f"Ruta fuera del proyecto: {entry['path']}")
            continue
        if not path.is_file():
            failures.append(f"Ausente: {entry['path']}")
            continue
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if path.stat().st_size != entry["bytes"] or actual != entry["sha256"]:
            failures.append(f"Distinto del manifiesto: {entry['path']}")
    core_reference = ROOT / "reproducibility" / "FROZEN_CORE_REFERENCE.json"
    active = ROOT / "reproducibility" / "ACTIVE_CORE_REFERENCE.json"
    if active.exists():
        core_reference = active
    reference = json.loads(core_reference.read_text(encoding="utf-8"))
    for archived_path, expected in reference.items():
        relative = archived_path.replace("analyzer/", "", 1)
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"Falta módulo del núcleo congelado: {relative}")
            continue
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            failures.append(f"El núcleo no coincide con la instantánea científica: {relative}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Integridad comprobada: {len(data['files'])} archivos.")
    print(f"Núcleo científico vigente comprobado: {len(reference)} módulos.")
    print("Esto verifica identidad de archivos, no corrección científica ni la campaña completa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
