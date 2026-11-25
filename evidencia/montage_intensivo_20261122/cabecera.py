from pathlib import Path
import json

from MontagePy.main import mImgtbl, mMakeHdr


root = Path(__file__).resolve().parent
table = root / "imagenes.tbl"
header = root / "RESULTADOS" / "mosaico.hdr"
expected = len(json.loads((header.parent / "ENTRADAS.json").read_text()))
indexed = mImgtbl(str(root / "entradas_sia"), str(table))
print(indexed, flush=True)
if int(indexed["status"]) != 0 or int(indexed["count"]) != expected:
    raise RuntimeError(f"Montage debía indexar {expected} entradas")
made = mMakeHdr(str(table), str(header))
print(made, flush=True)
if int(made["status"]) != 0 or not header.is_file():
    raise RuntimeError("Montage no generó la cabecera")
