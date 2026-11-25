#!/usr/bin/env python3
"""Convierte los logs de una corrida en una tabla de tiempos.

Lee, sin volver a ejecutar nada:
  - jobstate.log          (Pegasus/DAGMan: SUBMIT, EXECUTE, JOB_TERMINATED, POST_SCRIPT_*)
  - history.long          (HTCondor: TransferInStarted/Finished, TransferOutStarted/Finished, máquina, CPU)
  - *.dag.metrics         (DAGMan: duración total)

Escribe:
  - jobs.csv      una fila por job: cada tramo de su vida, en segundos
  - corridas.csv  una fila por corrida: la duración total partida en tramos que suman el total

Uso:
  python3 tabla_tiempos.py --corrida NOMBRE CARPETA_CON_LOGS [--corrida NOMBRE2 CARPETA2 ...] --salida CARPETA
  python3 tabla_tiempos.py --lista corridas.txt --salida CARPETA      (cada línea: nombre;condición;carpeta)

Resolución: HTCondor y Pegasus registran los eventos en segundos enteros, así que cada tramo
tiene una incertidumbre de ±1 s. Un tramo de 0 s significa "menos de un segundo".
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from collections import defaultdict

AUX_PREFIXES = ("create_dir", "stage_in", "stage_out", "cleanup", "register", "chmod")

# Orden de prioridad para repartir cada segundo del flujo en una sola categoría.
CATEGORIAS = [
    ("ejecucion", "Ejecución de tareas"),
    ("transferencia", "Transferencias CondorIO"),
    ("auxiliares", "Jobs auxiliares de Pegasus"),
    ("cola", "Tareas esperando máquina"),
    ("cierre_post", "Cierre y post-script de Pegasus"),
    ("dagman", "DAGMan esperando para enviar"),
]


def find_one(folder: str, pattern: str) -> str | None:
    hits = sorted(glob.glob(os.path.join(folder, "**", pattern), recursive=True))
    return hits[0] if hits else None


def read_jobstate(path: str):
    events = defaultdict(dict)
    dag_start = dag_end = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 3:
                continue
            ts = int(parts[0])
            if parts[1] == "INTERNAL":
                if "DAGMAN_STARTED" in line:
                    dag_start = ts if dag_start is None else min(dag_start, ts)
                if "DAGMAN_FINISHED" in line:
                    dag_end = ts
                continue
            node, event = parts[1], parts[2]
            events[node].setdefault(event, ts)  # primera vez que ocurre
            if event in ("POST_SCRIPT_SUCCESS", "POST_SCRIPT_FAILURE", "JOB_TERMINATED", "JOB_SUCCESS"):
                events[node][event] = ts  # última vez
    return events, dag_start, dag_end


def read_history(path: str):
    jobs = {}
    if not path:
        return jobs
    text = open(path, encoding="utf-8", errors="replace").read()
    for block in re.split(r"\n\s*\n", text):
        attrs = {}
        for line in block.splitlines():
            if " = " in line:
                key, value = line.split(" = ", 1)
                attrs[key.strip()] = value.strip()
        node = attrs.get("DAGNodeName", "").strip('"')
        if node:
            jobs[node] = attrs
    return jobs


def num(attrs, key):
    try:
        return int(float(attrs[key]))
    except (KeyError, ValueError):
        return None


def bytes_from_stats(raw: str | None) -> int | None:
    if not raw:
        return None
    total = 0
    found = False
    for m in re.finditer(r"(\w+?)SizeBytesLastRun\s*=\s*(\d+)", raw):
        total += int(m.group(2))
        found = True
    return total if found else None


def analyze(name: str, condition: str, folder: str):
    jobstate = find_one(folder, "jobstate.log")
    history = find_one(folder, "history.long")
    metrics = find_one(folder, "*.dag.metrics")
    if not jobstate:
        raise SystemExit(f"{name}: falta jobstate.log en {folder}")
    events, dag_start, dag_end = read_jobstate(jobstate)
    hist = read_history(history)
    total_metrics = None
    if metrics:
        with open(metrics, encoding="utf-8") as fh:
            metric_values = json.load(fh)
            total_metrics = metric_values.get("duration")
            if total_metrics is None:
                total_metrics = metric_values["end_time"] - metric_values["start_time"]

    rows = []
    intervals = defaultdict(list)  # categoría -> [(inicio, fin)]
    for node, ev in events.items():
        aux = node.startswith(AUX_PREFIXES)
        h = hist.get(node, {})
        submit = ev.get("SUBMIT")
        execute = ev.get("EXECUTE")
        terminated = ev.get("JOB_TERMINATED")
        success = ev.get("JOB_SUCCESS")
        post_end = ev.get("POST_SCRIPT_SUCCESS") or ev.get("POST_SCRIPT_FAILURE") or success
        tin_s, tin_f = num(h, "TransferInStarted"), num(h, "TransferInFinished")
        tout_s, tout_f = num(h, "TransferOutStarted"), num(h, "TransferOutFinished")
        start = num(h, "JobCurrentStartDate") or execute
        row = dict(
            corrida=name, condicion=condition, job=node,
            tipo="auxiliar" if aux else "tarea",
            maquina=(h.get("LastRemoteHost", "").strip('"').split("@")[-1] or ("dme-master" if aux else "")),
            cpu_usuario_s=h.get("CumulativeRemoteUserCpu", ""),
            bytes_entrada=bytes_from_stats(h.get("TransferInputStats")),
            bytes_salida=bytes_from_stats(h.get("TransferOutputStats")),
            t_envio=submit, t_inicio=start, t_fin_entrada=tin_f, t_inicio_salida=tout_s,
            t_fin_salida=tout_f, t_terminado=terminated, t_fin_post=post_end,
        )

        def d(a, b):
            return (b - a) if (a is not None and b is not None) else None

        row.update(
            espera_maquina_s=d(submit, tin_s if tin_s is not None else start),
            transferencia_entrada_s=d(tin_s, tin_f),
            ejecucion_s=d(tin_f, tout_s) if not aux else d(execute, terminated),
            transferencia_salida_s=d(tout_s, tout_f),
            cierre_s=d(tout_f if tout_f is not None else terminated, post_end),
            vida_total_s=d(submit, post_end),
        )
        rows.append(row)

        if aux:
            if submit is not None and post_end is not None:
                intervals["auxiliares"].append((submit, post_end))
            continue
        if submit is not None and tin_s is not None:
            intervals["cola"].append((submit, tin_s))
        if tin_s is not None and tin_f is not None:
            intervals["transferencia"].append((tin_s, tin_f))
        if tin_f is not None and tout_s is not None:
            intervals["ejecucion"].append((tin_f, tout_s))
        if tout_s is not None and tout_f is not None:
            intervals["transferencia"].append((tout_s, tout_f))
        if tout_f is not None and post_end is not None:
            intervals["cierre_post"].append((tout_f, post_end))

    if dag_start is None:
        dag_start = min(r["t_envio"] for r in rows if r["t_envio"] is not None)
    if dag_end is None:
        dag_end = max(r["t_fin_post"] for r in rows if r["t_fin_post"] is not None)

    # Reparte cada segundo [dag_start, dag_end) en la categoría de mayor prioridad activa.
    tally = {key: 0 for key, _ in CATEGORIAS}
    for t in range(dag_start, dag_end):
        chosen = "dagman"
        for key, _ in CATEGORIAS[:-1]:
            if any(a <= t < b for a, b in intervals[key]):
                chosen = key
                break
        tally[chosen] += 1

    tasks = [r for r in rows if r["tipo"] == "tarea"]

    def total(key):
        return sum(r[key] for r in tasks if r[key] is not None)

    first_task = min((r["t_envio"] for r in tasks if r["t_envio"] is not None), default=None)
    exec_starts = [r["t_fin_entrada"] for r in tasks if r["t_fin_entrada"] is not None]
    exec_ends = [r["t_inicio_salida"] for r in tasks if r["t_inicio_salida"] is not None]
    summary = dict(
        corrida=name, condicion=condition,
        duracion_dagman_s=total_metrics,
        duracion_jobstate_s=dag_end - dag_start,
        diferencia_resolucion_s=(total_metrics - (dag_end - dag_start)) if total_metrics is not None else None,
        **{f"tramo_{k}_s": v for k, v in tally.items()},
        tareas=len(tasks), auxiliares=len(rows) - len(tasks),
        suma_ejecucion_tareas_s=total("ejecucion_s"),
        suma_transferencia_entrada_s=total("transferencia_entrada_s"),
        suma_transferencia_salida_s=total("transferencia_salida_s"),
        suma_espera_maquina_s=total("espera_maquina_s"),
        suma_cierre_s=total("cierre_s"),
        bytes_transferidos=sum((r["bytes_entrada"] or 0) + (r["bytes_salida"] or 0) for r in tasks),
        preparacion_hasta_primera_tarea_s=(first_task - dag_start) if first_task else None,
        ventana_ejecucion_s=(max(exec_ends) - min(exec_starts)) if exec_starts and exec_ends else None,
    )
    return rows, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corrida", nargs=2, action="append", metavar=("NOMBRE", "CARPETA"), default=[])
    ap.add_argument("--lista", help="archivo con líneas nombre;condición;carpeta")
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    runs = [(n, "", f) for n, f in args.corrida]
    if args.lista:
        for line in open(args.lista, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                n, c, f = [x.strip() for x in line.split(";")]
                runs.append((n, c, f))
    os.makedirs(args.salida, exist_ok=True)
    all_rows, summaries = [], []
    for name, cond, folder in runs:
        rows, summary = analyze(name, cond, folder)
        all_rows += rows
        summaries.append(summary)
    for fname, data in (("jobs.csv", all_rows), ("corridas.csv", summaries)):
        with open(os.path.join(args.salida, fname), "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
    print(f"{len(summaries)} corridas, {len(all_rows)} jobs -> {args.salida}")


if __name__ == "__main__":
    main()
