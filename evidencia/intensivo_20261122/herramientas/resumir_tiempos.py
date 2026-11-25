#!/usr/bin/env python3
"""Resume corridas.csv por condición: promedio y desviación estándar muestral de cada tramo.

Uso: python3 resumir_tiempos.py CARPETA_CON_corridas.csv
Escribe resumen.csv en la misma carpeta.
"""
import csv
import os
import statistics as st
import sys
from collections import defaultdict

COLUMNAS = [
    "duracion_dagman_s", "tramo_ejecucion_s", "tramo_transferencia_s", "tramo_auxiliares_s",
    "tramo_cola_s", "tramo_cierre_post_s", "tramo_dagman_s", "suma_ejecucion_tareas_s",
    "suma_transferencia_entrada_s", "suma_transferencia_salida_s", "ventana_ejecucion_s",
    "preparacion_hasta_primera_tarea_s", "bytes_transferidos",
]

folder = sys.argv[1]
rows = list(csv.DictReader(open(os.path.join(folder, "corridas.csv"), encoding="utf-8")))
groups = defaultdict(list)
for row in rows:
    groups[row["condicion"]].append(row)
out = []
for cond, rs in sorted(groups.items()):
    rec = {"condicion": cond, "n": len(rs)}
    for col in COLUMNAS:
        vals = [float(r[col]) for r in rs if r.get(col) not in ("", "None", None)]
        rec[col + "_prom"] = round(st.mean(vals), 2) if vals else ""
        rec[col + "_desv"] = round(st.stdev(vals), 2) if len(vals) > 1 else ""
    out.append(rec)
with open(os.path.join(folder, "resumen.csv"), "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    writer.writeheader()
    writer.writerows(out)
print(f"resumen de {len(out)} condiciones -> {folder}/resumen.csv")
