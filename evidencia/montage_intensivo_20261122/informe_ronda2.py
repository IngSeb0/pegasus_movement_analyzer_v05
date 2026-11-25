import csv
from datetime import datetime
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


root = Path(__file__).resolve().parent
first = root / "RESULTADOS"
out = root / "ronda2_50mbit"
consolidator = (root / "consolidar_sia.py").read_text()
consolidator = consolidator.split("windows = []")[0].replace(
    'parent / "RESULTADOS"', 'parent / "ronda2_50mbit"')
exec(compile(consolidator, str(root / "consolidar_sia.py"), "exec"), {"__file__": __file__})


def table(path):
    if path.is_file():
        with path.open(newline="") as stream:
            return list(csv.DictReader(stream))
    return []


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


columns = ("transferencia", "ejecucion", "auxiliares", "cola", "cierre_post", "dagman")
labels = ("Transferencia CondorIO", "Ejecución", "Jobs auxiliares", "Espera de máquina",
          "Cierre y post-script", "Espera de DAGMan")


def num(value, digits=2):
    return f"{float(value):,.{digits}f}".replace(",", " ").replace(".", ",")


def get_pilot(folder):
    row = next((row for row in table(folder / "corridas.csv") if row["fase"] == "pilot"), {})
    band = read(folder / "ANCHO_DE_BANDA.json")
    return row, band


p1, b1 = get_pilot(first)
p2, b2 = get_pilot(out)
decision = read(out / "PILOTO.json")
matrix = read(out / "evidencia_nativa" / "MATRIZ_DECISION.json")
differences = table(out / "diferencias_por_bloque.csv")
summary = table(out / "resumen.csv")
volumes = table(out / "BYTES.csv")
main = [row for row in volumes if row["fase"] == "main"]
by_condition = {key: [r for r in main if r["condicion"] == key] for key in ("MG-BASE", "MG-FINAL")}
complete = bool(matrix) and all(len(runs) == matrix["bloques"] for runs in by_condition.values())
fits = read(out / "EQUIVALENCIA_FITS.json")
delta = read(out / "PREDICCIONES.json")["delta_observed_bytes"]
expected = delta / b2["entrada"]["bytes_por_s"] if b2 else None
if expected is not None:
    path = out / "PREDICCIONES.json"
    prediction = read(path)
    prediction["tiempo"].update(entrada_medida_bytes_s=b2["entrada"]["bytes_por_s"],
                                salida_medida_bytes_s=b2["salida"]["bytes_por_s"],
                                delta_observado_s_calibrado=expected)
    path.write_text(json.dumps(prediction, indent=2))

lines = ["# Montage M101 · Ronda enmendada a 50 Mbit/s", "",
         "Se conservaron los planes, las 147 imágenes y las hipótesis selladas. El límite de red se cambió después de conocer el piloto a 100 Mbit/s.", "",
         "## Comparación de los pilotos", "",
         "| Medida | 100 Mbit/s | 50 Mbit/s |", "| --- | ---: | ---: |"]
for name, direction in (("Ancho de banda de entrada (Mbit/s)", "entrada"),
                        ("Ancho de banda de salida (Mbit/s)", "salida")):
    values = [num(band[direction]["bytes_por_s"] * 8e-6) if band else "—" for band in (b1, b2)]
    lines.append(f"| {name} | {values[0]} | {values[1]} |")
for label, key in [("Duración DAGMan (s)", "duracion_dagman_s"),
                   *((label + " (s)", f"tramo_{column}_s") for label, column in zip(labels, columns))]:
    values = [num(row[key], 3 if key == "duracion_dagman_s" else 0) if key in row else "—" for row in (p1, p2)]
    lines.append(f"| {label} | {values[0]} | {values[1]} |")
if decision:
    msg = "superó el criterio" if decision["intensivo_en_datos"] else "activó la parada"
    lines.extend(["", f"El piloto a 50 Mbit/s {msg}."])
    if p1 and p2:
        change = float(p2["tramo_transferencia_s"]) - float(p1["tramo_transferencia_s"])
        lines.append(f"Entre los dos pilotos el tramo de transferencia aumentó {num(change, 0)} s. "
                     "La estimación previa de 578 s era una aproximación basada en duplicar el primer tramo. "
                     "La comparación entre límites usa un piloto por límite y es descriptiva.")
else:
    lines.extend(["", "La ronda terminó antes de obtener un dictamen del piloto."])
lines.extend(["", "## Matriz", "", f"Se conservaron {len(main)} corridas principales auditadas."])
if matrix:
    lines.append(f"El presupuesto permitió programar {matrix['bloques']} bloques rotados.")
if expected is not None:
    lines.append(f"Los planes prevén un ahorro de {num(delta, 0)} B, equivalente a {num(expected)} s con la tasa de entrada medida.")
if main:
    lines.extend(["", "| Variante | Requerido (B) | Observado (B) | DME exacta |", "| --- | ---: | ---: | ---: |"])
    for condition, records in by_condition.items():
        signatures = {(row["requerido_B"], row["observado_B"], row["DME"]) for row in records}
        for required, observed, dme in sorted(signatures):
            lines.append(f"| {condition} | {num(required, 0)} | {num(observed, 0)} | {dme} |")
if summary:
    lines.extend(["", "| Variante | Medida | n | Promedio ± desviación (s) |",
                  "| --- | --- | ---: | ---: |"])
    for row in summary:
        dev = num(row["desviacion_s"]) if row["desviacion_s"] else "—"
        lines.append(f"| {row['condicion']} | {row['medida']} | {row['n']} | {num(row['promedio_s'])} ± {dev} |")
if differences:
    lines.extend(["", "| Bloque | BASE − FINAL en transferencia (s) | BASE − FINAL total (s) |",
                  "| --- | ---: | ---: |"])
    for block in sorted({r["bloque"] for r in differences}):
        by_key = {r["medida"]: r["base_menos_final_s"] for r in differences if r["bloque"] == block}
        lines.append(f"| {block} | {num(by_key['tramo_transferencia_s'])} | {num(by_key['duracion_dagman_s'])} |")
    transfer = [float(r["base_menos_final_s"]) for r in differences if r["medida"] == "tramo_transferencia_s"]
    elapsed = [float(r["base_menos_final_s"]) for r in differences if r["medida"] == "duracion_dagman_s"]
    if transfer and elapsed:
        lines.extend(["", f"El ahorro medio por bloque fue {num(sum(transfer) / len(transfer))} s en transferencia "
                      f"y {num(sum(elapsed) / len(elapsed))} s en duración total. "
                      "La agrupación reúne en W1 dos tareas que ya eran consecutivas por dependencia."])
lines.extend(["", "El reparto temporal asigna cada segundo a un solo tramo. Los segundos de ejecución corresponden a tiempo de pared de los jobs según esa clasificación.", "",
              "Los registros por corrida están en `evidencia_nativa/`. El cierre y la red se documentan en `VMS.md` y `TC.txt`."])
(out / "RESUMEN_RESULTADOS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

verdict = ["# Contraste M1–M5 · 50 Mbit/s", ""]
if complete:
    required_sets = {r["requerido_B"] for r in main}
    observed = {k: {int(r["observado_B"]) for r in rows} for k, rows in by_condition.items()}
    m1 = len(required_sets) == 1 and observed == {"MG-BASE": {4360834806}, "MG-FINAL": {3744673019}}
    verdict.append(f"- M1 {'Sí' if m1 else 'No'}. Requerido {required_sets.pop() if len(required_sets) == 1 else required_sets} B; observado por variante {observed}.")
    m2 = len(fits) == 2 and all(row["coinciden"] for row in fits.values())
    verdict.append(f"- M2 {'Sí' if m2 else 'No'}. Comparación SHA-256 del mosaico y del mapa de área en `EQUIVALENCIA_FITS.json`.")
else:
    verdict.extend(["- M1 Pendiente de la comparación completa entre variantes. El cotejo de planes se conserva.",
                    "- M2 Pendiente de la comparación completa de los archivos finales."])
timed = table(out / "corridas.csv")
if timed:
    qualified = sum(float(row["tramo_transferencia_s"]) >
                    max(float(row[f"tramo_{key}_s"]) for key in columns[1:]) for row in timed)
    verdict.append(f"- M3 {'Sí' if qualified == len(timed) else 'No'} en las corridas observadas del régimen enmendado. Cumplieron {qualified} de {len(timed)}.")
else:
    verdict.append("- M3 Pendiente. Falta el desglose temporal del piloto a 50 Mbit/s.")
for hypothesis, key in (("M4", "tramo_transferencia_s"), ("M5", "duracion_dagman_s")):
    values = [float(row["base_menos_final_s"]) for row in differences if row["medida"] == key]
    if complete and values and (key != "tramo_transferencia_s" or expected is not None):
        success = all(0.75 * expected <= x <= 1.25 * expected for x in values) if hypothesis == "M4" else all(x > 0 for x in values)
        detail = f" Predicción ΔO/B de {num(expected)} s, tolerancia ±25 %." if hypothesis == "M4" else ""
        verdict.append(f"- {hypothesis} {'Sí' if success else 'No'}. Diferencias BASE − FINAL de {', '.join(num(x) for x in values)} s.{detail}")
    else:
        verdict.append(f"- {hypothesis} Pendiente. No hay una matriz completa de tiempos por bloque.")
(out / "CONTRASTE_HIPOTESIS.md").write_text("\n".join(verdict) + "\n", encoding="utf-8")

closed = out / "sesion09"
states = json.loads((closed / "estado_final.json").read_text(encoding="utf-8-sig"))
assert len(states) == 5 and all(vm["state"] == "VM deallocated" for vm in states)
start, stop = (datetime.fromisoformat((closed / f"{k}_utc.txt").read_text().strip()[:26]) for k in ("inicio", "cierre"))
window = (stop - start).total_seconds()
previous = 0.0
for s in sorted(root.glob("sesion*")) + sorted(out.glob("sesion*")):
    if s == closed:
        continue
    if not (s / "cierre_utc.txt").exists():
        continue
    a, b = (datetime.fromisoformat((s / f"{k}_utc.txt").read_text().strip()[:26]) for k in ("inicio", "cierre"))
    previous += (b - a).total_seconds()
network = (out / "TC.txt").read_text(encoding="utf-8") if (out / "TC.txt").exists() else ""
checks = [chunk.split("\n\n", 1)[0] for chunk in network.split(" después ")[1:]]
cleared = len(checks) == 5 and all(" tbf " not in check.split("\ndme-", 1)[0] for check in checks)
(out / "VMS.md").write_text(
    f"# Cierre de Azure\n\nAzure confirmó las cinco VMs desasignadas. El acceso SSH temporal se retiró. "
    f"Ventana de la ronda {num(window, 3)} s. Acumulado de las dos rondas y su preparación "
    f"{num(previous + window, 3)} s de 18 000 s. "
    + ("TC.txt confirma la retirada de tbf en los cinco nodos.\n" if cleared
       else "TC.txt y TC_ERRORES.json documentan el alcance de la comprobación de red.\n"),
    encoding="utf-8",
)
(out / "CAMBIOS.md").write_text(
    "# Cambios de la ronda\n\nLa enmienda cambia el límite de 100 a 50 Mbit/s. "
    "Se conservan las entradas y el diseño congelado y se mantiene separada la evidencia de ambos pilotos. "
    "La matriz conserva el criterio de parada, orden rotado y límite de 45 minutos por corrida. "
    "La primera ventana de la ronda cerró antes de aplicar tc por un nombre incorrecto del paquete. "
    "Se corrigió y el tiempo de esa ventana se incluyó en el presupuesto.\n",
    encoding="utf-8",
)
package = out / "Montage_M101_Ronda2_50Mbit_20261122.zip"
with ZipFile(package, "w", ZIP_DEFLATED) as archive:
    for file in out.rglob("*"):
        if file.is_file() and file != package and file.name not in {"ssh_config", "regla_temporal.json", "evidencia.tar.gz"}:
            archive.write(file, file.relative_to(out))
    for name in ("planes_nativos.tar.gz", "PLAN_ACCOUNTS.json", "DISENO_CONGELADO.json", "ENTRADAS.json", "SIA_2MASS_J.xml",
                 "mosaico.hdr", "PILOTO.json", "ANCHO_DE_BANDA.json", "corridas.csv", "BYTES.csv"):
        archive.write(first / name, "ronda_100mbit/" + name)
    for file in (first / "evidencia_nativa").rglob("*"):
        if file.is_file():
            archive.write(file, Path("ronda_100mbit") / file.relative_to(first))
with ZipFile(package) as archive:
    assert archive.testzip() is None
