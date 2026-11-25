#!/usr/bin/env python3
"""La tarea científica sintética que ejecuta cada job en un worker.

Pegasus escribe los argumentos de cada job, por ejemplo:
    tarea.py --task-id T1 --flops 1766799020 --input A 209715200 --output g 209715200
Lee cada entrada completa, hace la carga de cómputo (fma_kernel.c) y escribe cada salida.
"""
import argparse, hashlib, subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--task-id", required=True)
p.add_argument("--flops", required=True)
p.add_argument("--input", nargs=2, action="append", default=[])    # NOMBRE BYTES
p.add_argument("--output", nargs=2, action="append", required=True)
a = p.parse_args()

for nombre, tam in a.input:                       # 1. leer cada entrada y comprobar su tamaño
    leido = 0
    with open(nombre, "rb") as f:
        while bloque := f.read(1 << 20):
            leido += len(bloque)
    assert leido == int(tam), f"{nombre}: leí {leido} B y esperaba {tam}"

Path("fma_kernel").chmod(0o755)                   # 2. carga de cómputo: operaciones FMA
print(subprocess.run(["./fma_kernel", "--flops", a.flops],
                     check=True, capture_output=True, text=True).stdout)

for nombre, tam in a.output:                      # 3. escribir cada salida con su tamaño exacto
    bloque = hashlib.shake_256(f"{a.task_id}/{nombre}".encode()).digest(1 << 20)
    restante = int(tam)
    with open(nombre, "wb") as f:
        while restante:
            f.write(bloque[:restante])
            restante -= min(restante, len(bloque))
