"""Recompute defense figures from the verified capsule audits and native DAG logs."""

from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tarfile

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / "evidence"
SYNTHETIC = BASE.parent / "validacion_cinco_patrones_20261110"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def timing(case):
    with tarfile.open(SYNTHETIC / "evidence" / (case + ".tar.xz")) as archive:
        item, = (m for m in archive if m.name.endswith("/jobstate.log"))
        lines = archive.extractfile(item).read().decode().splitlines()
    def timestamp(match):
        return min(int(line.split()[0]) for line in lines if match(line))
    first_submit = timestamp(lambda line: "campaign_task_" in line and " SUBMIT " in line)
    first_exec = timestamp(lambda line: "campaign_task_" in line and " EXECUTE " in line)
    start = timestamp(lambda line: "DAGMAN_STARTED" in line)
    return {"submit_at_s": first_submit - start, "first_execute_at_s": first_exec - start,
            "first_submit_to_execute_s": first_exec - first_submit}


def main():
    trials = read(EVIDENCE / "RESULTS.json")
    assert [trial["id"] for trial in trials] == ["M101-BASE", "M101-PROJ", "M101-FINAL"]
    assert read(EVIDENCE / "FITS_EQUIVALENCE.json")["matches"]
    assert read(EVIDENCE / "COMPLETE.json")["accepted"] == 3
    actual = {}
    transfers = {}
    for trial in trials:
        name = trial["id"]
        audit_file = EVIDENCE / "audits" / (name + ".json")
        audit = read(audit_file) if audit_file.exists() else None
        capsule = EVIDENCE / "capsules" / (name + ".tar.xz")
        if capsule.exists():
            with capsule.open("rb") as stream:
                assert hashlib.file_digest(stream, "sha256").hexdigest() == read(capsule.with_suffix(".sha256.json"))["sha256"]
            with tarfile.open(capsule) as archive:
                preserved_audit = json.load(archive.extractfile(f"pilot/{name}/INDEPENDENT_AUDIT.json"))
            assert audit is None or audit == preserved_audit
            audit = preserved_audit
        assert audit is not None
        assert not audit["errors"] and all(d["residual"] == 0 and d["exact"] for d in audit["directions"])
        required = sum(row["bytes"] * len(row["destinations"]) for row in audit["files"].values())
        observed = sum(row["bytes"] for row in audit["deliveries"])
        assert (required, observed) == (trial["required_bytes"], trial["observed_bytes"])
        assert Fraction(required, observed) == Fraction(trial["dme"])
        actual[name] = dict(required=required, observed=observed, dme=trial["dme"], jobs=len(audit["jobs"]),
                            directions=len(audit["directions"]), duration=trial["duration_s"],
                            deliveries=trial["deliveries"], obligations=trial["obligations"])
        transfers[name] = Counter((row["file"], row["direction"], row["source"], row["destination"], row["bytes"])
                                  for row in audit["deliveries"])
    baseline = actual["M101-BASE"]
    for name in ("M101-PROJ", "M101-FINAL"):
        avoided = transfers["M101-BASE"] - transfers[name]
        assert not transfers[name] - transfers["M101-BASE"]
        savings = sum(row[-1] * count for row, count in avoided.items())
        assert savings == baseline["observed"] - actual[name]["observed"]
        actual[name].update(savings=savings, relative_savings=savings / baseline["observed"],
                            avoided=[[*row, count] for row, count in sorted(avoided.items())])
    assert actual["M101-FINAL"]["observed"] < actual["M101-PROJ"]["observed"] < baseline["observed"]
    assert len({trial["required"] for trial in actual.values()}) == 1
    selected = {case: timing(case) for case in ("AGGREGATION-W2", "AGGREGATION-W4", "REDISTRIBUTION-W2", "REDISTRIBUTION-W4")}
    summary = dict(montage=actual, timing=selected,
                   correctitude=read(SYNTHETIC / "VERIFICACION_REUNION.json"))
    (BASE / "VERIFICACION_DEFENSA.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    labels = {"M101-BASE": "Base sin agrupación", "M101-PROJ": "Dos reproyecciones juntas",
              "M101-FINAL": "Tabla y coadición juntas"}
    def bytes_text(value):
        return f"{value:,}".replace(",", "\u202f")
    lines = [
        "# Sensibilidad de DME en el mosaico M101", "",
        "El [tutorial oficial de Montage](https://irsa.ipac.caltech.edu/Montage/docs/m101tutorial.html) proporciona diez imágenes 2MASS J y la cabecera de destino. "
        "Se ejecutó la ruta de reproyección, tabla de imágenes y coadición hasta producir el mosaico FITS y su mapa de cobertura. "
        "Los tres casos conservaron el grafo de doce tareas, los parámetros, las entradas y la ubicación observada.", "",
        "| Configuración | Jobs científicos | Requerido (bytes) | Observado (bytes) | DME exacta | Duración (s) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, result in actual.items():
        duration = f"{result['duration']:.3f}".replace(".", ",")
        lines.append(f"| {labels[name]} | {result['jobs']} | {bytes_text(result['required'])} | "
                     f"{bytes_text(result['observed'])} | {result['dme']} | {duration} |")
    lines.extend(["", "Cada fila representa una ejecución. La duración es descriptiva.", "",
                  "## Entregas eliminadas frente a la base", "",
                  "| Configuración | Archivo | Dirección | Bytes ahorrados |",
                  "| --- | --- | --- | ---: |"])
    for name in ("M101-PROJ", "M101-FINAL"):
        for file, direction, origin, destination, size, count in actual[name]["avoided"]:
            lines.append(f"| {labels[name]} | `{file}` | {origin} → {destination} | {bytes_text(size * count)} |")
    lines.extend(["", f"Analyzer coincidió con la auditoría independiente en las tres ejecuciones. "
                  f"Se conciliaron {sum(result['directions'] for result in actual.values())} direcciones con residuo cero. "
                  "Los datos binarios de las imágenes y las tarjetas FITS comparadas, incluida la geometría, coincidieron con la referencia local.", "",
                  "La agrupación de tabla y coadición minimizó el observado entre las configuraciones ensayadas. "
                  "Se mantuvo la ruta del tutorial sin ajuste de fondo. El contraste no permite ordenar agrupaciones que quedaron fuera del diseño ni atribuir una mejora temporal a los bytes.", ""])
    (BASE / "RESULTADOS_M101.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(dict(montage=actual, timing=selected), indent=2))


if __name__ == "__main__":
    main()
