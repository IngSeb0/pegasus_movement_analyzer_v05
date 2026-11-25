from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


root = Path(__file__).resolve().parent
target = root / "Montage_M101_SIA_20261122.zip"
with ZipFile(target, "w", compression=ZIP_DEFLATED, compresslevel=5) as package:
    for path in sorted((root / "RESULTADOS").rglob("*")):
        if path.is_file():
            package.write(path, path.relative_to(root))
    for session in sorted(root.glob("sesion*")):
        for name in ("inicio_utc.txt", "limite_utc.txt", "cierre_utc.txt",
                     "estado_final.json", "regla_retirada_utc.txt"):
            path = session / name
            if path.is_file():
                package.write(path, path.relative_to(root))
    for name in ("sia.py", "cabecera.py", "design_sia.py", "mosaic_task.py", "planificar_sia.py",
                 "medir_sia.py", "consolidar_sia.py", "preparacion_planes.tar.gz"):
        path = root / name
        if path.is_file():
            package.write(path, Path("metodo") / name)

with ZipFile(target) as package:
    assert package.testzip() is None
