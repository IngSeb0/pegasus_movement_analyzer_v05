"""Restore the question mark mapping in Latin Modern Type 1 fonts from Tectonic."""

import argparse
from pathlib import Path
import re

from pypdf import PdfReader, PdfWriter

WRONG_MAPPING = re.compile(rb"(?m)^<BF>[ \t]+<00A3>$")


def correct_text_mapping(source: Path, target: Path) -> int:
    if source.resolve() == target.resolve():
        raise ValueError("Use distintos archivos de entrada y salida.")
    writer = PdfWriter(source, incremental=True)
    visited = set()
    changed = 0
    for page in writer.pages:
        fonts = page["/Resources"].get("/Font", {})
        for reference in fonts.values():
            font = reference.get_object()
            base_font = str(font.get("/BaseFont", "")).split("+")[-1]
            if font.get("/Subtype") != "/Type1" or not base_font.startswith(("LMRoman", "LMSans", "LMMono")):
                continue
            if "/ToUnicode" not in font:
                continue
            cmap = font["/ToUnicode"]
            if cmap.indirect_reference.idnum in visited:
                continue
            visited.add(cmap.indirect_reference.idnum)
            mapping, count = WRONG_MAPPING.subn(b"<BF> <00BF>", cmap.get_data())
            if count:
                cmap.set_data(mapping)
                changed += 1
    with target.open("wb") as output:
        writer.write(output)
    if changed:
        text = "".join(page.extract_text() for page in PdfReader(target).pages)
        if "£" in text or "¿" not in text:
            raise ValueError("No se pudo verificar la corrección de los signos.")
    return changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path)
    args = parser.parse_args()
    print(f"Mapas actualizados: {correct_text_mapping(args.entrada, args.salida)}")
