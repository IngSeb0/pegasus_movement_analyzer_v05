from pathlib import Path
import tarfile


suffixes = {".json", ".log", ".yml", ".yaml", ".sub", ".in", ".metrics",
            ".dag", ".long", ".csv", ".stdout", ".stderr", ".out", ".exit",
            ".xml", ".tsv", ".meta", ".hdr"}
with tarfile.open("evidencia.tar.gz", "w:gz") as archive:
    for file in Path(".").rglob("*"):
        if not file.is_file():
            continue
        name = file.name
        if file.suffix in suffixes or ".out." in name or ".err." in name:
            archive.add(file, arcname=file.as_posix())
