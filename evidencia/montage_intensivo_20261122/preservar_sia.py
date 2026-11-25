from hashlib import file_digest
import json
from pathlib import Path
import shutil
import time


source = Path("/mnt/montage_intensivo_20261122/sia")
target = Path.home() / "montage_intensivo_20261122"
destination = target / "entradas_sia"
destination.mkdir(parents=True, exist_ok=True)
seen = set()
deadline = time.monotonic() + 1800
manifest = source / "RESULTADOS" / "ENTRADAS.json"
while time.monotonic() < deadline:
    try:
        entries = json.loads(manifest.read_text())
    except (OSError, ValueError):
        time.sleep(1)
        continue
    for entry in entries:
        name = entry["nombre"]
        if name in seen:
            continue
        src = source / "entradas_sia" / name
        dst = destination / name
        shutil.copyfile(src, dst)
        with dst.open("rb") as stream:
            digest = file_digest(stream, "sha256").hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"Hash distinto en la copia persistente de {name}")
        seen.add(name)
    if len(seen) == 147:
        shutil.copytree(source / "RESULTADOS", target / "RESULTADOS", dirs_exist_ok=True)
        print(f"{len(seen)} FITS preservados y verificados", flush=True)
        break
    time.sleep(1)
else:
    raise TimeoutError(f"Se verificaron {len(seen)} FITS en el disco persistente")
