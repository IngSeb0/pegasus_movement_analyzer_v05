"""Prepara el flujo de Montage (M101, banda J de 2MASS, 2° x 2°): descarga las fotos y escribe la especificación.

    python3 montage.py carpeta [lado_en_grados]
    python3 crear_flujo.py carpeta/especificaciones.json MG-BASE   flujo_base      # o MG-FINAL

Corre en el coordinador (necesita internet y curl). Esta descarga ocurre antes del flujo y no cuenta en DME.
Si carpeta/entradas ya tiene fotos, no las vuelve a descargar.
"""
import base64, gzip, json, math, subprocess, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

carpeta = Path(sys.argv[1]).resolve()
lado = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
fotos = carpeta / "entradas"
fotos.mkdir(parents=True, exist_ok=True)
RA0, DEC0 = 210.802, 54.349                                   # centro de M101
SIA = "https://irsa.ipac.caltech.edu/cgi-bin/2MASS/IM/nph-im_sia"


def bajar(url, destino):
    subprocess.run(["curl", "-fsSL", "--retry", "3", "--retry-all-errors", "--max-time", "60",
                    "-o", str(destino), url], check=True)


# 1. Fotos: se pregunta a IRSA qué imágenes J cubren el cuadrado y se bajan una por una.
if not list(fotos.glob("*.fits")):
    bajar(SIA + "?" + urlencode(dict(POS=f"{RA0},{DEC0}", SIZE="2.0", band="J", type="at",
                                     ds="asky", FORMAT="image/fits")), carpeta / "catalogo.xml")
    tabla = ET.parse(carpeta / "catalogo.xml")
    if tabla.find(".//{*}INFO[@name='QUERY_STATUS']").get("value") != "OK":
        sys.exit("IRSA no devolvió QUERY_STATUS=OK")
    campos = [c.get("name") for c in tabla.findall(".//{*}FIELD")]
    for fila in tabla.findall(".//{*}TR"):
        r = dict(zip(campos, [c.text for c in fila.findall("{*}TD")]))
        if r["type"] != "A" or r["band"] != "J":
            continue
        # posición de la foto respecto al centro (proyección tangente); se queda si cae dentro del cuadrado
        ra, dec, d0 = math.radians(float(r["center_ra"]) - RA0), math.radians(float(r["center_dec"])), math.radians(DEC0)
        x = math.cos(dec) * math.sin(ra)
        y = math.cos(d0) * math.sin(dec) - math.sin(d0) * math.cos(dec) * math.cos(ra)
        z = math.sin(d0) * math.sin(dec) + math.cos(d0) * math.cos(dec) * math.cos(ra)
        if z > 0 and max(abs(math.degrees(math.atan2(x, z))), abs(math.degrees(math.atan2(y, z)))) <= lado / 2:
            nombre = r["coadd_key"].strip() + "_" + Path(parse_qs(urlsplit(r["download"]).query)["name"][0]).name
            destino = fotos / nombre
            bajar(r["download"], destino)
            datos = destino.read_bytes()
            datos = gzip.decompress(datos) if datos[:2] == b"\x1f\x8b" else datos
            if not datos.startswith(b"SIMPLE  ="):
                sys.exit(f"{nombre} no es un FITS")
            destino.write_bytes(datos)

# 2. MontagePy: la rueda se baja una vez; con ella se crea la cabecera común (template.hdr) que usarán
#    todas las alineaciones, y también viajará dentro de la tarea para que los workers la tengan.
subprocess.run([sys.executable, "-m", "pip", "download", "montagepy==2.3.0", "--no-deps", "--only-binary=:all:",
                "--python-version", f"{sys.version_info.major}.{sys.version_info.minor}",
                "--platform", "manylinux2014_x86_64", "-d", str(carpeta)], check=True)   # mismo Python que los workers (3.12)
rueda = next(carpeta.glob("montagepy-2.3.0-*.whl"))
zipfile.ZipFile(rueda).extractall(carpeta / ".montagepy")
sys.path.insert(0, str(carpeta / ".montagepy"))
from MontagePy.main import mImgtbl, mMakeHdr
if int(mImgtbl(str(fotos), str(carpeta / "fotos.tbl"))["status"]) or int(mMakeHdr(str(carpeta / "fotos.tbl"), str(fotos / "template.hdr"))["status"]):
    sys.exit("Montage no pudo crear la cabecera")
tarea = (Path(__file__).parent / "tarea_montage.py").read_text()
(carpeta / "tarea_montage.py").write_text(
    tarea.replace("WHEEL = None", "WHEEL = " + repr(base64.b64encode(rueda.read_bytes()).decode()), 1))

# 3. El flujo: P## alinea cada foto (una por foto, repartidas por turnos en W2, W3 y W4);
#    TABLE y ADD, en W1, indexan las alineadas y arman el mosaico.
nombres = sorted(p.name for p in fotos.glob("*.fits"))
tareas = [dict(task_id=f"P{i:02d}", maquina=f"dme-worker{2 + (i - 1) % 3}", input_files=[f, "template.hdr"],
               output_files=[f"p{i:02d}.fits", f"p{i:02d}_area.fits"]) for i, f in enumerate(nombres, 1)]
alineadas = [t["output_files"][0] for t in tareas]
tareas += [dict(task_id="TABLE", maquina="dme-worker1", input_files=alineadas, output_files=["images.tbl"]),
           dict(task_id="ADD", maquina="dme-worker1", input_files=[n for t in tareas for n in t["output_files"]]
                + ["images.tbl", "template.hdr"], output_files=["m101.fits", "m101_area.fits"])]
produce = {n: t["task_id"] for t in tareas for n in t["output_files"]}
lee = {}
for t in tareas:
    for n in t["input_files"]:
        lee.setdefault(n, []).append(t["task_id"])
tamano = {p.name: p.stat().st_size for p in fotos.iterdir()}               # los intermedios no se conocen: 0
archivos = [dict(file_id=n, size_bytes=tamano.get(n, 0)) for n in sorted(set(produce) | set(lee))]
base = dict(programa="tarea_montage.py", entradas="entradas", files=archivos,
            dag=dict(tasks=tareas, external_inputs=sorted(set(lee) - set(produce)),
                     final_outputs=sorted(set(produce) - set(lee)),
                     edges=[dict(producer_task=produce[n], consumer_task=c) for n in produce for c in lee.get(n, [])]))
# BASE: TABLE y ADD son jobs separados. FINAL: Pegasus los agrupa en un solo job (así las alineadas no viajan dos veces).
(carpeta / "especificaciones.json").write_text(json.dumps(
    {"MG-BASE": dict(base, groups=[]), "MG-FINAL": dict(base, groups=[["TABLE", "ADD"]])}, indent=1))
print(f"{len(nombres)} fotos, {sum(tamano[n] for n in nombres)} B; especificación en {carpeta / 'especificaciones.json'}")
