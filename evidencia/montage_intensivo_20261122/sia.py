import gzip
import hashlib
import json
import math
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit


root = Path(__file__).resolve().parent
results = root / "RESULTADOS"
results.mkdir(exist_ok=True)
images = root / "entradas_sia"
images.mkdir(exist_ok=True)
ra0, dec0 = 210.802, 54.349
endpoint = "https://irsa.ipac.caltech.edu/cgi-bin/2MASS/IM/nph-im_sia"


def fetch(url, path, retries):
    partial = path.with_suffix(path.suffix + ".part")
    subprocess.run(
        ["curl", "-fsSL", "--retry", str(retries), "--retry-all-errors",
         "--max-time", "60", "--output", str(partial), url],
        check=True,
    )
    partial.replace(path)


def select(side, path):
    catalog = ET.parse(path)
    if catalog.find(".//{*}INFO[@name='QUERY_STATUS']").get("value") != "OK":
        raise ValueError("IRSA no devolvió QUERY_STATUS=OK")
    fields = [field.get("name") for field in catalog.findall(".//{*}FIELD")]
    rows = []
    for row in catalog.findall(".//{*}TR"):
        record = dict(zip(fields, [cell.text for cell in row.findall("{*}TD")]))
        if record["type"] != "A" or record["band"] != "J":
            continue
        ra = math.radians(float(record["center_ra"]) - ra0)
        dec = math.radians(float(record["center_dec"]))
        origin = math.radians(dec0)
        x = math.cos(dec) * math.sin(ra)
        y = math.cos(origin) * math.sin(dec) - math.sin(origin) * math.cos(dec) * math.cos(ra)
        z = math.sin(origin) * math.sin(dec) + math.cos(origin) * math.cos(dec) * math.cos(ra)
        if z > 0 and max(abs(math.degrees(math.atan2(x, z))),
                         abs(math.degrees(math.atan2(y, z)))) <= side / 2:
            rows.append(record)
    return rows


def save(path, payload):
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    catalog_path = results / "SIA_2MASS_J.xml"
    query = dict(POS=f"{ra0},{dec0}", SIZE="2.0", band="J", type="at",
                 ds="asky", FORMAT="image/fits")
    fetch(endpoint + "?" + urlencode(query), catalog_path, 3)
    side = 2.0
    rows = select(side, catalog_path)
    counts = {"2.0": len(rows)}
    if len(rows) > 250:
        side = 1.5
        rows = select(side, catalog_path)
        counts["1.5"] = len(rows)
    save(results / "SELECCION_SIA.json", {"query": query, "side": side, "counts": counts})
    if not 0 < len(rows) <= 250:
        raise ValueError(f"Cantidad de imágenes fuera del intervalo: {len(rows)}")
    entries = []
    for row in rows:
        url = row["download"]
        filename = Path(parse_qs(urlsplit(url).query)["name"][0]).name
        name = f'{row["coadd_key"].strip()}_{filename}'
        if not name or any(entry["nombre"] == name for entry in entries):
            raise ValueError(f"Nombre de FITS ambiguo: {name}")
        path = images / name
        # Tres intentos totales para cada imagen.
        fetch(url, path, 2)
        data = path.read_bytes()
        if data.startswith(b"\x1f\x8b"):
            data = gzip.decompress(data)
            path.write_bytes(data)
        if not data.startswith(b"SIMPLE  ="):
            raise ValueError(f"Respuesta sin cabecera FITS: {name}")
        entries.append({"nombre": name, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(), "url": url})
        save(results / "ENTRADAS.json", entries)
