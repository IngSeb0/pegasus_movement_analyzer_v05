"""Paquete para el cotejo previo de los planes de Montage."""

from base64 import b64encode
from io import BytesIO
from pathlib import Path
import tarfile


root = Path(__file__).resolve().parent
previous = root.parent / "montaje_m101_20261111" / "payload"
with tarfile.open(root / "preparacion_planes.tar.gz", "w:gz") as archive:
    for folder in ("runtime", "core"):
        for source in (previous / folder).rglob("*.py"):
            name = source.relative_to(previous).as_posix()
            if name != "runtime/run_study.py":
                archive.add(source, arcname=name)
                continue
            runner = source.read_text()
            runner = runner.replace(
                "'W2':'dme-worker2'", "'W2':'dme-worker2','W3':'dme-worker3','W4':'dme-worker4'"
            ).replace(
                "{'dme-worker1','dme-worker2'}",
                "{'dme-worker1','dme-worker2','dme-worker3','dme-worker4'}",
            ).replace("len(parents)==2", "len(parents)==4")
            runner = runner.replace("'-Xmx128m'", "'-Xmx512m'")
            runner = runner.replace("time.time()+800", "time.time()+2700")
            runner = runner.replace(
                " command(args,cwd=case,timeout=180,prefix=ev/'plan')",
                " planning_start=time.monotonic()\n"
                " command(args,cwd=case,timeout=180,prefix=ev/'plan')\n"
                " save(ev/'PLANIFICACION.json',dict(duration_s=time.monotonic()-planning_start))",
            )
            content = runner.encode()
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, BytesIO(content))
    for local, name in {
        "design_sia.py": "design_sia.py",
        "planificar_sia.py": "planificar_sia.py",
        "mosaic_task.py": "montage_assets/montage_task.py",
        "medir_sia.py": "medir_sia.py",
    }.items():
        if local == "mosaic_task.py":
            wheel_dir = root.parent / "pruebas_cierre_sin_cf_20261031" / "preparacion_montage"
            wheel = next(wheel_dir.glob("montagepy-2.3.0-*.whl"))
            program = (root / local).read_bytes().replace(b"\r\n", b"\n")
            program += f"\nWHEEL = {b64encode(wheel.read_bytes())!r}\n".encode()
            program += b"\nif __name__ == '__main__':\n    main()\n"
            info = tarfile.TarInfo(name)
            info.size = len(program)
            info.mode = 0o755
            archive.addfile(info, BytesIO(program))
        else:
            archive.add(root / local, arcname=name)
    timing = root.parent / "intensivo_20261122"
    archive.add(timing / "ejecutar.py", arcname="medir_banda.py")
    archive.add(timing / "herramientas" / "tabla_tiempos.py", arcname="tabla_tiempos.py")
