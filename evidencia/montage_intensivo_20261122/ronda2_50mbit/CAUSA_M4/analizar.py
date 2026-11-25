"""Reproduce la auditoría temporal de M4 desde los registros archivados."""
import csv
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import t
from statistics import stdev

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
NATIVE = ROOT / "evidencia_nativa"
sys.path.insert(0, str(ROOT.parents[1] / "intensivo_20261122" / "herramientas"))
import tabla_tiempos as original


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(name, rows):
    with (OUT / f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rate(bytes_, seconds):
    return round(8e-6 * bytes_ / seconds, 4) if seconds else None


def union(intervals):
    return set().union(*(set(range(start, stop)) for start, stop in intervals))


def phase(node):
    if node.startswith("stage_in"):
        return "stage_in"
    if node.startswith("merge_") or node.endswith(("_TABLE", "_ADD")):
        return "cierre_cientifico"
    return "proyecciones"


def run(entry):
    label, condition = entry["id"], entry["condition"]
    folder = NATIVE / "cases" / label
    jobstate = next(folder.rglob("jobstate.log"))
    dag = next(folder.rglob("*.dag"))
    events, start, stop = original.read_jobstate(str(jobstate))
    long = original.read_history(str(next(folder.rglob("history.long"))))
    ads = {ad["DAGNodeName"]: ad for ad in read(next(folder.rglob("history.json")))
           if ad.get("DAGNodeName")}
    window = set(range(start, stop))
    execution, auxiliary = set(), set()
    jobs = []
    for node, ev in events.items():
        aux = node.startswith(original.AUX_PREFIXES)
        submit = ev.get("SUBMIT")
        end = ev.get("POST_SCRIPT_SUCCESS") or ev.get("POST_SCRIPT_FAILURE") or ev.get("JOB_SUCCESS")
        if aux and submit is not None and end is not None:
            auxiliary.update(range(submit, end))
        ad = ads.get(node, {})
        h = long.get(node, {})
        a, b, c, d = [ad.get(key) for key in
                       ("TransferInStarted", "TransferInFinished", "TransferOutStarted", "TransferOutFinished")]
        if not aux:
            assert all(v is not None for v in (a, b, c, d))
            assert a <= b <= c <= d, (label, node, a, b, c, d)
            execution.update(range(b, c))
        for direction, lo, hi, stat in (("entrada", a, b, "TransferInputStats"),
                                         ("salida", c, d, "TransferOutputStats")):
            size = (ad.get(stat) or {}).get("CedarSizeBytesLastRun")
            assert size == original.bytes_from_stats(h.get(stat)), (label, node, stat)
            jobs.append(dict(corrida=label, job=node, auxiliar=aux, fase=phase(node), direccion=direction,
                             worker=ad.get("LastRemoteHost", "").split("@")[-1],
                             inicio_s=lo-start if lo is not None else None,
                             fin_s=hi-start if hi is not None else None,
                             duracion_s=hi-lo if lo is not None and hi is not None else None,
                             bytes=size, tasa_mbit_s=rate(size, hi-lo) if size is not None and lo is not None and hi is not None else None,
                             espera_envio_inicio_entrada_s=lo-submit if direction == "entrada" and lo is not None and submit is not None else None))

    def segments(rows):
        return [(j["inicio_s"] + start, j["fin_s"] + start) for j in rows
                if j["inicio_s"] is not None and j["fin_s"] is not None]

    science = [j for j in jobs if not j["auxiliar"]]
    trans = union(segments(science)) & window
    spans = {name: union(segments([j for j in science if j["fase"] == name])) & window
             for name in ("proyecciones", "cierre_cientifico")}
    pure = trans - execution - auxiliary
    auxwin = trans & auxiliary - execution
    published = read(next(folder.rglob("TIEMPOS.json")))
    assert len(trans-execution) == published["tramo_transferencia_s"] == len(pure)+len(auxwin)
    assert sum(j["bytes"] or 0 for j in science) == published["bytes_transferidos"]
    row = dict(corrida=label, condicion=condition, bloque=entry["block"], submittedAtUtc=entry["submittedAtUtc"],
               tramo_s=len(trans-execution), union_s=len(trans), solapa_ejecucion_s=len(trans & execution),
               solo_transferencia_s=len(pure), solapa_aux_gana_transferencia_s=len(auxwin),
               proyecciones_union_s=len(spans["proyecciones"]),
               cierre_union_s=len(spans["cierre_cientifico"]),
               ambas_fases_s=len(spans["proyecciones"] & spans["cierre_cientifico"]),
               cierre_asignado_s=len(spans["cierre_cientifico"] - execution),
               bytes_cientificos_y_aux_de_jobs_cientificos=published["bytes_transferidos"],
               diferencia_resolucion_s=published["diferencia_resolucion_s"],
               maxjobs_stagein=re.search(r"(?mi)^MAXJOBS\s+stagein\s+(\d+)", dag.read_text()).group(1),
               nodos_stagein=sum(node.startswith("stage_in") for node in events))
    stagein = [j for j in jobs if j["fase"] == "stage_in" and j["direccion"] == "entrada"]
    sts = union((events[j["job"]]["SUBMIT"], events[j["job"]].get("POST_SCRIPT_SUCCESS") or
                 events[j["job"]]["JOB_SUCCESS"]) for j in stagein)
    stage_counts = Counter(second for j in stagein for second in
                           range(events[j["job"]]["SUBMIT"], events[j["job"]].get("POST_SCRIPT_SUCCESS")
                                 or events[j["job"]]["JOB_SUCCESS"]))
    row.update(stagein_vida_union_s=len(sts), stagein_solapa_transferencia_s=len(sts & trans),
               stagein_max_vidas=max(stage_counts.values(), default=0))
    rates = []
    for name, selected in [
        ("entrada", [j for j in science if j["direccion"] == "entrada"]),
        ("salida", [j for j in science if j["direccion"] == "salida"]),
        ("proyecciones_entrada", [j for j in science if j["fase"] == "proyecciones" and j["direccion"] == "entrada"]),
        ("proyecciones_salida", [j for j in science if j["fase"] == "proyecciones" and j["direccion"] == "salida"]),
        ("cierre_entrada", [j for j in science if j["fase"] == "cierre_cientifico" and j["direccion"] == "entrada"]),
        ("cierre_salida", [j for j in science if j["fase"] == "cierre_cientifico" and j["direccion"] == "salida"]),
    ]:
        concurrency = Counter(second for a, b in segments(selected) for second in range(a, b))
        bytes_ = sum(j["bytes"] or 0 for j in selected)
        total = sum(concurrency.values())
        waits = [j["espera_envio_inicio_entrada_s"] for j in selected if j["espera_envio_inicio_entrada_s"] is not None]
        rates.append(dict(corrida=label, grupo=name, bytes=bytes_, union_s=len(concurrency), suma_job_s=total,
                          tasa_union_mbit_s=rate(bytes_, len(concurrency)), tasa_job_ponderada_mbit_s=rate(bytes_, total),
                          max_concurrencia=max(concurrency.values(), default=0),
                          segundos_con_2_o_mas=sum(n >= 2 for n in concurrency.values()),
                          cero_s_con_bytes=sum(j["duracion_s"] == 0 and bool(j["bytes"]) for j in selected),
                          espera_mediana_s=sorted(waits)[len(waits)//2] if waits else None))
    return row, jobs, rates


runs, jobs, rates = [], [], []
for entry in read(NATIVE / "LEDGER.json"):
    row, items, groups = run(entry)
    runs.append(row)
    jobs.extend(items)
    rates.extend(groups)
for i, row in enumerate(runs):
    row["orden"] = i + 1
    row["anterior"] = runs[i-1]["corrida"] if i else ""
    row["min_desde_primer_envio"] = (datetime.fromisoformat(row["submittedAtUtc"]) -
                                     datetime.fromisoformat(runs[0]["submittedAtUtc"])).total_seconds() / 60
    row["base_o_final_primero"] = next(r["condicion"] for r in runs if r["bloque"] == row["bloque"])

fields = ("tramo_s", "union_s", "solapa_ejecucion_s", "solo_transferencia_s",
          "solapa_aux_gana_transferencia_s", "proyecciones_union_s", "cierre_union_s",
          "ambas_fases_s", "cierre_asignado_s", "bytes_cientificos_y_aux_de_jobs_cientificos")
pairs = []
for block in (1, 2, 3):
    base, final = sorted((r for r in runs if r["bloque"] == block), key=lambda r:r["condicion"])
    pairs.append(dict(bloque=block, primero=base["base_o_final_primero"],
                      **{field: base[field] - final[field] for field in fields}))

write("corridas_intervalos", runs)
write("jobs_intervalos", jobs)
write("tasas_concurrencia", rates)
write("bloques_descomposicion", pairs)
quartiles = []
for row in runs:
    for direction in ("entrada", "salida"):
        selection = sorted((j for j in jobs if j["corrida"] == row["corrida"] and not j["auxiliar"]
                            and j["fase"] == "proyecciones" and j["direccion"] == direction),
                           key=lambda j: j["inicio_s"])
        for q in range(4):
            sample = selection[q*len(selection)//4:(q+1)*len(selection)//4]
            intervals = union((j["inicio_s"], j["fin_s"]) for j in sample)
            total = sum(j["bytes"] or 0 for j in sample)
            quartiles.append(dict(corrida=row["corrida"], direccion=direction, cuartil=q+1,
                                  jobs=len(sample), bytes=total, union_s=len(intervals),
                                  tasa_grupo_mbit_s=rate(total, len(intervals)),
                                  tasa_job_ponderada_mbit_s=rate(total, sum(j["duracion_s"] for j in sample))))
write("tasas_por_cuartil", quartiles)
band = read(ROOT / "ANCHO_DE_BANDA.json")["entrada"]["bytes_por_s"]
delta = read(ROOT / "PREDICCIONES.json")["delta_observed_bytes"]
std = stdev(r["tramo_s"] for r in pairs)
threshold = .25 * delta / band
write("precision_muestra", [dict(n=n, desviacion_s=std, margen_objetivo_s=threshold,
                                semiancho_t95_s=t.ppf(.975,n-1) * std / n**.5)
                            for n in range(3, 41)])

fig, axes = plt.subplots(2, 2, figsize=(13, 8), layout="constrained")
labels = [r["corrida"].replace("MG-", "") for r in runs]
x = list(range(len(runs)))
ax = axes[0,0]
ax.bar(x, [r["solo_transferencia_s"] for r in runs], label="Sin ejecución ni auxiliares")
ax.bar(x, [r["solapa_aux_gana_transferencia_s"] for r in runs],
       bottom=[r["solo_transferencia_s"] for r in runs], label="Con auxiliares, sin ejecución")
ax.bar(x, [r["solapa_ejecucion_s"] for r in runs], bottom=[r["tramo_s"] for r in runs],
       label="Solapada con ejecución")
ax.set(title="Unión temporal de transferencias", ylabel="Segundos")
ax.legend(fontsize=8)
ax = axes[0,1]
for name in ("entrada", "salida", "cierre_entrada"):
    ax.plot(x, [next(r["tasa_union_mbit_s"] for r in rates if r["corrida"] == run["corrida"] and r["grupo"] == name)
               for run in runs], marker="o", label=name)
ax.axhline(8e-6*band, color="gray", linestyle="--", label="Calibración entrada")
ax.set(title="Bytes / unión de intervalos por dirección", ylabel="Mbit/s")
ax.legend(fontsize=8)
ax = axes[1,0]
for name in ("entrada", "salida"):
    ax.bar([i + (-.18 if name=="entrada" else .18) for i in x],
           [r["segundos_con_2_o_mas"] for r in rates if r["grupo"] == name], width=.35, label=name)
ax.set(title="Tiempo con dos o más transferencias simultáneas", ylabel="Segundos")
ax.legend()
for ax in (axes[0,0], axes[0,1], axes[1,0]):
    ax.set_xticks(x,labels, rotation=28)
ax = axes[1,1]
for field, label in (("tramo_s","Tramo publicado"), ("union_s","Unión sin prioridad"), ("cierre_union_s","Solo unión del cierre")):
    ax.plot([1,2,3], [r[field] for r in pairs], marker="o", label=label)
ax.axhspan(.75*delta/band,1.25*delta/band,color="grey",alpha=.18,label="Predicción ±25 %")
ax.set(title="Ahorro BASE − FINAL", xlabel="Bloque", ylabel="Segundos", xticks=[1,2,3])
ax.legend(fontsize=8)
fig.savefig(OUT / "diagnostico_m4.png", dpi=175)
