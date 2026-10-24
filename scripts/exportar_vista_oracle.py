"""Exporta la vista en vivo a CSV y comprueba su lectura completa."""

import csv
import hashlib
import json
from pathlib import Path

from capturar_vista_oracle import read_view

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = read_view()
    headers = [c["columna"].lower() for c in source["columnas"]]
    rows = sorted(source["filas"], key=lambda r: r["registro_id"])
    serialized = [["" if row[c] is None else str(row[c]) for c in headers] for row in rows]
    folder = ROOT / "data/exports/taller_2"
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / "Caso2_Oracle_Admisiones.csv"
    tmp = out.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=",", lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(serialized)
    with tmp.open(encoding="utf-8-sig", newline="") as handle:
        parsed = list(csv.reader(handle))
    assert parsed[0] == headers and parsed[1:] == serialized
    assert len(headers) == 15 and len(rows) == len({r["registro_id"] for r in rows})
    tmp.replace(out)
    info = {
        "origen": "CASO2.V_ADMISIONES_BASE",
        "consultado_en": source["consultado_en"],
        "archivo": str(out.relative_to(ROOT)),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "filas_sin_encabezado": len(rows),
        "columnas": len(headers),
        "codificacion": "UTF-8 con BOM",
        "separador": ",",
        "separador_decimal": ".",
        "fechas": "YYYY-MM-DD",
        "nulos": "Celda vacía. El CSV no mantiene los tipos ni diferencia NULL de texto vacío.",
        "orden": "registro_id ascendente para facilitar la comparación",
        "verificacion": "Lectura CSV igual a las 15 columnas serializadas de todas las filas consultadas en vivo.",
        "metadatos_oracle": source["columnas"],
        "alcance": "Exportación sin limpieza ni integración con las otras fuentes. Copia de consulta, sin refresco automático.",
    }
    (folder / "Caso2_Oracle_Admisiones.metadata.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"Exportado y verificado: {out.relative_to(ROOT)}; {len(rows)} filas y {len(headers)} columnas.")


if __name__ == "__main__":
    main()
