"""Exporta la hoja consolidada a CSV y Excel con valores, sin nueva limpieza."""

import argparse
from collections import Counter
import csv
from datetime import date, datetime
import hashlib
from io import BytesIO
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from zoneinfo import ZoneInfo

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]


def serialized(value):
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def preserve_empty_text(path, rows):
    """Mantiene texto vacío distinto de celda ausente en el Excel nuevo.

    openpyxl omite el elemento inlineStr de los textos vacíos al guardar.
    Se completa solo esa serialización para conservar los valores del origen.
    """
    positions = [f"{get_column_letter(j)}{i}" for i, row in enumerate(rows, 2) for j, value in enumerate(row, 1) if value == ""]
    if not positions:
        return
    namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ET.register_namespace("", namespace)
    with ZipFile(path) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    patched = []
    for info, data in entries:
        if info.filename == "xl/worksheets/sheet1.xml":
            root = ET.fromstring(data)
            cells_by_position = {cell.attrib["r"]: cell for cell in root.iter(f"{{{namespace}}}c")}
            for pos in positions:
                cell = cells_by_position[pos]
                cell.attrib["t"] = "inlineStr"
                for child in list(cell):
                    cell.remove(child)
                inline = ET.SubElement(cell, f"{{{namespace}}}is")
                ET.SubElement(inline, f"{{{namespace}}}t").text = ""
            data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        patched.append((info, data))
    with ZipFile(path, "w") as archive:
        for info, data in patched:
            archive.writestr(info, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data/BaseUnificada_Manejo.xlsx")
    parser.add_argument("--sheet", default="BaseUnificada_ConProgramas_Merg")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/prepared/taller_2")
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    book = load_workbook(BytesIO(source_bytes), read_only=True, data_only=True)
    if args.sheet not in book.sheetnames:
        raise ValueError(f"No existe la hoja {args.sheet}. Hojas: {book.sheetnames}")
    sheet = book[args.sheet]
    cells = list(sheet.iter_rows())
    headers = [c.value for c in cells[0]]
    if not all(isinstance(h, str) and h for h in headers) or len(headers) != len(set(headers)):
        raise ValueError("Los encabezados deben ser únicos y no vacíos")
    errors = [c.coordinate for row in cells[1:] for c in row if c.data_type == "e"]
    if errors:
        raise ValueError(f"La hoja contiene celdas de error: {errors[:10]}")
    rows = [tuple(c.value for c in row) for row in cells[1:]]
    if not rows:
        raise ValueError("No hay registros para exportar")
    expected_headers = ["registro_id", "aspirante_id", "fecha_solicitud", "programa", "modalidad", "canal_captacion", "estado_proceso", "puntaje_admision", "documentos_completos", "valor_matricula_cop", "ciudad_residencia", "asesor", "fecha_matricula", "correo", "periodo_academico", "facultad", "duracion_semestres", "nivel_formacion"]
    if headers != expected_headers:
        raise ValueError("La hoja no tiene las 18 columnas acordadas. Revisar antes de exportar.")
    book.close()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "BaseUnificada.csv"
    xlsx_path = args.output_dir / "BaseUnificada.xlsx"
    csv_tmp = csv_path.with_suffix(".csv.tmp")
    xlsx_tmp = xlsx_path.with_name("BaseUnificada.tmp.xlsx")
    csv_rows = [[serialized(v) for v in row] for row in rows]
    with csv_tmp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(csv_rows)
    output_book = Workbook()
    output_sheet = output_book.active
    output_sheet.title = "BaseUnificada"
    output_sheet.append(headers)
    for row in rows:
        output_sheet.append(row)
    last = f"{get_column_letter(len(headers))}{len(rows) + 1}"
    table = Table(displayName="BaseUnificada", ref=f"A1:{last}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    output_sheet.add_table(table)
    output_sheet.freeze_panes = "A2"
    for i, header in enumerate(headers, 1):
        output_sheet.column_dimensions[get_column_letter(i)].width = min(38, max(18, len(header) + 3))
    output_book.save(xlsx_tmp)
    output_book.close()
    preserve_empty_text(xlsx_tmp, rows)
    with csv_tmp.open(encoding="utf-8-sig", newline="") as handle:
        actual_csv = list(csv.reader(handle))
    if actual_csv != [headers, *csv_rows]:
        raise RuntimeError("El CSV no coincide con todas las filas serializadas")
    checked = load_workbook(xlsx_tmp, read_only=True, data_only=True)
    actual_excel = list(checked["BaseUnificada"].iter_rows(values_only=True))
    if list(actual_excel[0]) != headers or actual_excel[1:] != rows:
        raise RuntimeError("El Excel exportado no coincide con los valores de la hoja original")
    checked.close()
    if hashlib.sha256(args.source.read_bytes()).digest() != hashlib.sha256(source_bytes).digest():
        raise RuntimeError("El libro origen cambió durante la exportación. Repetir tras guardar Excel.")
    csv_tmp.replace(csv_path)
    xlsx_tmp.replace(xlsx_path)
    result = {
        "exportado_en": datetime.now(ZoneInfo("America/Bogota")).isoformat(),
        "libro_origen": str(args.source.resolve().relative_to(ROOT)),
        "hoja_origen": args.sheet,
        "sha256_libro_origen": hashlib.sha256(source_bytes).hexdigest(),
        "filas_sin_encabezado": len(rows),
        "columnas": len(headers),
        "encabezados": headers,
        "registros_id_distintos": len({r[0] for r in rows}),
        "filas_facultad_sin_asignar": sum(r[15] in (None, "") for r in rows),
        "periodos": dict(Counter(serialized(r[14]) for r in rows)),
        "archivos": {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in [csv_path, xlsx_path]},
        "verificacion": {"excel_igual_a_todos_los_valores_del_origen": True, "csv_igual_a_todas_las_filas_serializadas": True, "libro_origen_sin_modificar": True},
        "csv": {"codificacion": "UTF-8 con BOM", "separador": ",", "decimal": ".", "ausencias": "Celdas vacías; no mantiene distinción entre NULL y texto vacío ni tipos Excel"},
        "alcance": "Punto de partida para la siguiente limpieza. No se corrigen fechas, periodos, valores, categorías ni duplicados. Excel sin consultas ni vínculos: valores de la hoja guardada.",
    }
    (args.output_dir / "BaseUnificada.metadata.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"filas": len(rows), "columnas": len(headers), "archivos": [str(csv_path.relative_to(ROOT)), str(xlsx_path.relative_to(ROOT))], "validacion_completa": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
