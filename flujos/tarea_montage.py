#!/usr/bin/env python3
"""Tarea de Montage que corre en el worker: P## alinea una foto, TABLE indexa las alineadas, ADD las suma.

Uso (lo arma crear_flujo.py):  --task-id P01 --input NOMBRE BYTES ... --output NOMBRE BYTES ...
BYTES = 0 significa «tamaño desconocido, no comprobar».
"""
import argparse, base64, io, sys, zipfile
from pathlib import Path

WHEEL = None          # montage.py pone aquí MontagePy (base64), para que el worker no necesite instalarlo

ap = argparse.ArgumentParser()
ap.add_argument("--task-id", required=True)
ap.add_argument("--input", nargs=2, action="append", required=True)
ap.add_argument("--output", nargs=2, action="append", required=True)
a = ap.parse_args()
for nombre, tamano in a.input:
    if int(tamano) and Path(nombre).stat().st_size != int(tamano):
        raise ValueError(f"La entrada {nombre} no tiene el tamaño esperado")

# MontagePy viaja dentro de este script: se desempaca y se importa.
libreria = Path(".montagepy-" + a.task_id)
zipfile.ZipFile(io.BytesIO(base64.b64decode(WHEEL))).extractall(libreria)
sys.path.insert(0, str(libreria.resolve()))
from MontagePy.main import mAdd, mImgtbl, mProjectPP

if a.task_id.startswith("P"):                      # P##: alinea una foto a la cabecera común
    foto = next(n for n, _ in a.input if n.endswith(".fits"))
    salida = next(n for n, _ in a.output if not n.endswith("_area.fits"))
    r = mProjectPP(foto, salida, "template.hdr")
else:                                              # TABLE y ADD trabajan sobre las alineadas
    marcos = Path(".marcos-" + a.task_id)
    marcos.mkdir()
    for nombre, _ in a.input:
        if nombre.endswith(".fits"):
            (marcos / nombre).symlink_to(Path(nombre).resolve())
    if a.task_id == "TABLE":
        r = mImgtbl(str(marcos), "images.tbl")
    else:
        r = mAdd(str(marcos), "images.tbl", "template.hdr", "m101.fits")
if int(r["status"]) != 0:
    raise RuntimeError(r)
print(a.task_id, r)
